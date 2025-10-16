# ai_chart_summary.py
# Full working version: PaddleX → JSON → Structured Table → Nova Lite natural summary

import os
import json
import pandas as pd
from paddlex import create_model
import boto3
from botocore.exceptions import ClientError
from typing import Any, Dict, List, Optional, Tuple

# ===========================
# Bedrock (Nova Lite) Client
# ===========================
class ChartAnalyzerWithBedrock:
    def __init__(self, region_name: str = 'eu-west-1'):
        self.region_name = region_name
        try:
            self.bedrock = boto3.client('bedrock-runtime', region_name=region_name)
            print(f"✅ AWS Bedrock initialized in region: {region_name}")
        except Exception as e:
            print(f"❌ Failed to initialize Bedrock: {str(e)}")
            self.bedrock = None

    def get_ai_summary(self, table_data: pd.DataFrame, chart_context: str = "", raw_json: Optional[str] = None):
        """Generate a natural-language summary of the data using Nova Lite (Bedrock)."""
        if not self.bedrock:
            return "AI summary unavailable – Bedrock not initialized."

        try:
            csv_preview = table_data.to_csv(index=False)
            prompt = f"""
You are an expert data analyst. Summarize the dataset in simple natural language.

Context: {chart_context}

Below is the dataset extracted from a chart:
{csv_preview}

If it represents categories (like colours, years, etc.), describe the trend:
- Mention which category has the highest and lowest values.
- Explain key differences or observations.
- Write in clear English, as if explaining to a manager.
- Be concise (4–6 sentences).

Also, if you can infer what this data might represent (e.g., "Number of students per colour category"), mention that briefly.

{f"Raw JSON for reference:\n{raw_json}" if raw_json else ""}
            """

            response = self.bedrock.converse(
                modelId="eu.amazon.nova-lite-v1:0",
                messages=[{
                    "role": "user",
                    "content": [{"text": prompt}]
                }],
                inferenceConfig={
                    "maxTokens": 500,
                    "temperature": 0.7,
                    "topP": 0.9
                }
            )

            out = response.get("output", {})
            msg = out.get("message", {})
            content = msg.get("content", [])
            if content and isinstance(content, list) and "text" in content[0]:
                return content[0]["text"]
            return json.dumps(response, ensure_ascii=False)[:1000]

        except ClientError as e:
            return f"Error getting AI summary: {e}"
        except Exception as e:
            return f"Unexpected error: {e}"

# ===========================
# Data Helpers
# ===========================
def parse_pipe_table(text: str) -> Optional[pd.DataFrame]:
    """Parse '|' delimited table text into DataFrame."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if len(lines) < 2:
        return None

    rows = []
    for line in lines:
        parts = [p.strip() for p in line.split('|')]
        if parts and parts[0] == "":
            parts = parts[1:]
        if parts and parts[-1] == "":
            parts = parts[:-1]
        rows.append(parts)

    header = rows[0]
    data_rows = rows[1:]
    data_rows = [r + [''] * (len(header) - len(r)) for r in data_rows]
    df = pd.DataFrame(data_rows, columns=header)

    # Convert numeric-like values
    for col in df.columns:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace('%', ''), errors='ignore')
    return df

def generate_summary(df: pd.DataFrame) -> Dict[str, Any]:
    summary = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'columns': [str(c) for c in df.columns],
        'key_insights': []
    }

    numeric_cols = df.select_dtypes(include=['number']).columns
    for col in numeric_cols:
        col_series = pd.to_numeric(df[col], errors='coerce')
        summary['key_insights'].append({
            'column': str(col),
            'min': float(col_series.min(skipna=True) or 0),
            'max': float(col_series.max(skipna=True) or 0),
            'mean': float(col_series.mean(skipna=True) or 0),
            'total': float(col_series.sum(skipna=True) or 0)
        })
    return summary

# ===========================
# Main Chart Processing
# ===========================
def process_chart_results_with_ai(results, analyzer):
    summaries = []
    os.makedirs("./output", exist_ok=True)

    for i, res in enumerate(results):
        json_path = f"./output/res_{i}.json"
        if hasattr(res, "save_to_json"):
            res.save_to_json(json_path)
        else:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(res, f, indent=2)

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        raw_json = json.dumps(data, ensure_ascii=False)[:4000]
        table_data = None
        if isinstance(data, dict) and 'result' in data:
            table_data = parse_pipe_table(data['result'])

        if table_data is not None:
            table_data.to_csv(f"./output/table_{i}.csv", index=False)
            print(f"\n=== STRUCTURED TABLE {i} ===")
            print(table_data.to_string(index=False))

            summary = generate_summary(table_data)
            print("\n🧠 Generating natural AI summary...")
            ai_summary = analyzer.get_ai_summary(table_data, f"Chart result {i}", raw_json)
            summary['ai_summary'] = ai_summary

            print(f"\n📋 AI Summary for Result {i}:\n{ai_summary}\n")
            summaries.append(summary)
        else:
            print(f"⚠️ No table found in result {i}")

    with open('./output/ai_enhanced_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summaries, f, indent=2, ensure_ascii=False)
    print("\n💾 Saved: ./output/ai_enhanced_summary.json")

def main():
    print("🔥 Chart → Table → AI Summarizer 🔥")
    default_path = r"C:\Users\kumamay1\OneDrive - acuitykp\Work\ChartModel\Paddle\Sample_Image2.png"
    img_path = input(f"Enter image path [{default_path}]: ").strip() or default_path

    if not os.path.exists(img_path):
        print("❌ Image not found.")
        return

    print("\n🔍 Running PaddleX model...")
    model = create_model("PP-Chart2Table", device="cpu")
    results = model.predict(input={"image": img_path}, batch_size=1)

    analyzer = ChartAnalyzerWithBedrock(region_name='eu-west-1')
    process_chart_results_with_ai(results, analyzer)
    print("\n✅ Done! Check the ./output folder for results.")

if __name__ == "__main__":
    main()