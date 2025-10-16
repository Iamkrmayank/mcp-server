# ai_enhanced_chart_analyzer.py
# End-to-end: PaddleX chart → JSON → structured table → Bedrock (Nova Lite) insights → saved outputs

import os
import re
import json
import pandas as pd

from typing import List, Tuple, Optional, Any, Dict

# External deps
#   pip install paddlex boto3
from paddlex import create_model
import boto3
from botocore.exceptions import ClientError

# ===========================
# Bedrock: AI Analyzer
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

    def _prepare_data_summary(self, df: pd.DataFrame) -> str:
        if df is None or df.empty:
            return "No data available"

        summary = []
        summary.append(f"Dataset: {len(df)} rows, {len(df.columns)} columns")
        summary.append(f"Columns: {', '.join(df.columns.astype(str).tolist())}")

        # Numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            summary.append("\nNumeric Data:")
            for col in numeric_cols:
                stats = df[col].describe()
                # Use safe access for stats
                try:
                    mn = stats['min']
                    mx = stats['max']
                    mean = stats['mean']
                except Exception:
                    mn, mx, mean = df[col].min(), df[col].max(), df[col].mean()
                summary.append(f"  {col}: min={mn}, max={mx}, mean={float(mean):.2f}")

        # Categorical columns
        categorical_cols = df.select_dtypes(include=['object', 'string']).columns
        if len(categorical_cols) > 0:
            summary.append("\nCategorical Data:")
            for col in categorical_cols:
                unique_vals = df[col].dropna().unique().tolist()
                if len(unique_vals) <= 10:
                    summary.append(f"  {col}: {', '.join(map(str, unique_vals))}")
                else:
                    summary.append(f"  {col}: {len(unique_vals)} unique values")

        # Sample data
        summary.append("\nSample Data (first 3 rows):")
        try:
            summary.append(df.head(3).to_string(index=False))
        except Exception:
            summary.append(str(df.head(3)))

        return '\n'.join(summary)

    def _extract_nova_text(self, payload: Dict[str, Any]) -> str:
        # Typical Nova-lite chat format
        try:
            out = payload.get('output', {})
            msg = out.get('message', {})
            content = msg.get('content', [])
            if content and isinstance(content, list):
                candidate = content[0]
                if isinstance(candidate, dict) and 'text' in candidate:
                    return candidate['text']
        except Exception:
            pass
        # fallback: trimmed JSON for debugging
        return json.dumps(payload, ensure_ascii=False)[:2000]

    def get_ai_insights(self, table_data: pd.DataFrame, chart_context: str = "") -> str:
        if not self.bedrock:
            return "AI insights unavailable - Bedrock not initialized"
        try:
            data_summary = self._prepare_data_summary(table_data)
            prompt = f"""
You are a data analyst. Analyze the following chart data and provide insights:

Context: {chart_context}

Data Summary:
{data_summary}

Please provide:
1) Key trends and patterns
2) Notable data points or outliers
3) Business insights and recommendations
4) Data quality observations

Keep the analysis concise but insightful.
""".strip()

            response = self.bedrock.invoke_model(
                modelId="eu.amazon.nova-lite-v1:0",
                contentType="application/json",
                accept="application/json",
                body=json.dumps({
                    "messages": [
                        {
                            "role": "user",
                            "content": [{"text": prompt}]
                        }
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.7
                })
            )

            raw = response.get('body')
            payload = json.loads(raw.read()) if hasattr(raw, 'read') else json.loads(raw)
            return self._extract_nova_text(payload)

        except ClientError as e:
            return f"Error getting AI insights: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"


# ===========================
# Parsing Helpers
# ===========================
def parse_pipe_table(text: str) -> Optional[pd.DataFrame]:
    """
    Parse a simple pipe-delimited table (as in your earlier JSON)
    Example 'result' string:
      "Year | metric1 | metric2\n2018 | 10 | 20\n2019 | 11 | 21"
    """
    if not text or not isinstance(text, str):
        return None

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if len(lines) < 2:
        return None

    rows = []
    for line in lines:
        parts = [p.strip() for p in line.split('|')]
        # Drop leading/trailing empty cells if surrounded by pipes
        if parts and parts[0] == '':
            parts = parts[1:]
        if parts and parts[-1] == '':
            parts = parts[:-1]
        rows.append(parts)

    header = rows[0]
    data_rows = rows[1:]

    # Normalize row length to header length
    fixed = []
    for r in data_rows:
        if len(r) < len(header):
            r = r + [''] * (len(header) - len(r))
        elif len(r) > len(header):
            r = r[:len(header)]
        fixed.append(r)

    df = pd.DataFrame(fixed, columns=header)

    # Try to coerce numeric/percentage columns
    for col in df.columns:
        if df[col].dtype == 'object':
            # Remove % then try numeric
            df[col] = df[col].astype(str).str.replace('%', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='ignore')

    return df


def flatten_json(json_obj: Any, parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    """Flatten nested JSON structure into a single dict."""
    items = []
    if isinstance(json_obj, dict):
        for k, v in json_obj.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_json(v, new_key, sep=sep).items())
            elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                for i, item in enumerate(v):
                    items.extend(flatten_json(item, f"{new_key}{sep}{i}", sep=sep).items())
            else:
                items.append((new_key, v))
    return dict(items)


def generate_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute summary stats used in the final printout/JSON."""
    summary = {
        'total_rows': int(len(df)),
        'total_columns': int(len(df.columns)),
        'columns': [str(c) for c in df.columns],
        'key_insights': [],
        'categories': []
    }

    numeric_cols = df.select_dtypes(include=['number']).columns
    for col in numeric_cols:
        try:
            summary['key_insights'].append({
                'column': str(col),
                'min': float(pd.to_numeric(df[col], errors='coerce').min(skipna=True)),
                'max': float(pd.to_numeric(df[col], errors='coerce').max(skipna=True)),
                'mean': float(pd.to_numeric(df[col], errors='coerce').mean(skipna=True)),
                'total': float(pd.to_numeric(df[col], errors='coerce').sum(skipna=True))
            })
        except Exception:
            pass

    categorical_cols = df.select_dtypes(include=['object', 'string']).columns
    for col in categorical_cols:
        vals = df[col].dropna().unique().tolist()
        summary['categories'].append({
            'column': str(col),
            'unique_values_preview': [str(v) for v in vals[:20]],
            'count': int(len(vals))
        })

    return summary


# ===========================
# Core: From PaddleX results → JSON → Structured → AI
# ===========================
def create_table_and_summary_with_ai(
    json_data: Any,
    result_index: int,
    analyzer: ChartAnalyzerWithBedrock
) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
    """
    Accepts the parsed JSON (from res.save_to_json file), creates a table, and gets AI insights.
    Handles your earlier 'result' pipe-string shape too.
    """
    table_data = None
    summary = {
        'result_index': result_index,
        'chart_type': 'Unknown',
        'ai_insights': '',
        'key_insights': [],
        'total_rows': 0,
        'total_columns': 0,
        'columns': [],
        'categories': []
    }

    try:
        # 1) Your earlier JSON shape: {"image": "...", "result": "<pipe table string>"}
        if isinstance(json_data, dict) and isinstance(json_data.get('result'), str):
            table_data = parse_pipe_table(json_data['result'])

        # 2) Generic "table" or "data"
        if table_data is None:
            if isinstance(json_data, dict) and 'table' in json_data:
                table_data = pd.DataFrame(json_data['table'])
            elif isinstance(json_data, dict) and 'data' in json_data:
                if isinstance(json_data['data'], list):
                    table_data = pd.DataFrame(json_data['data'])
                elif isinstance(json_data['data'], dict):
                    table_data = pd.DataFrame([json_data['data']])
            elif isinstance(json_data, list):
                table_data = pd.DataFrame(json_data)
            else:
                # 3) Fallback: flatten an arbitrary dict
                if isinstance(json_data, dict):
                    flat = flatten_json(json_data)
                    if flat:
                        table_data = pd.DataFrame([flat])

        # Coerce percent-like text to numbers (remove %)
        if table_data is not None and not table_data.empty:
            for c in table_data.columns:
                if table_data[c].dtype == 'object':
                    try:
                        table_data[c] = (
                            table_data[c]
                            .astype(str)
                            .str.replace('%', '', regex=False)
                        )
                        table_data[c] = pd.to_numeric(table_data[c], errors='ignore')
                    except Exception:
                        pass

            # Fill summary stats
            summary.update(generate_summary(table_data))

            # AI insights
            print(f"🤖 Generating AI insights for result {result_index}...")
            chart_context = f"Chart analysis result {result_index}"
            summary['ai_insights'] = analyzer.get_ai_insights(table_data, chart_context)

            # Show structured table in console
            print(f"\n=== STRUCTURED TABLE {result_index} ===")
            try:
                print(table_data.to_string(index=False))
            except Exception:
                print(table_data.head())

            # Save CSV
            os.makedirs("./output", exist_ok=True)
            csv_path = f"./output/table_{result_index}.csv"
            table_data.to_csv(csv_path, index=False)
            print(f"📄 Table saved to: {csv_path}")
        else:
            print(f"⚠️ Could not create table from result {result_index}")

    except Exception as e:
        print(f"❌ Error processing result {result_index}: {str(e)}")
        summary['ai_insights'] = f"Error generating insights: {str(e)}"

    return table_data, summary


def process_chart_results_with_ai(results: Any, analyzer: ChartAnalyzerWithBedrock) -> Tuple[List[pd.DataFrame], List[Dict[str, Any]]]:
    """
    Iterate PaddleX results, persist to JSON, reload JSON, structure + AI summarize.
    Works whether each item is an object with save_to_json(...) or plain dict already.
    """
    all_tables: List[pd.DataFrame] = []
    all_summaries: List[Dict[str, Any]] = []

    os.makedirs("./output", exist_ok=True)

    for i, res in enumerate(results):
        print(f"\n---- Processing Result {i} ----")
        json_path = f"./output/res_{i}.json"

        # Try to save to JSON using PaddleX result object
        saved = False
        try:
            if hasattr(res, "save_to_json"):
                res.save_to_json(json_path)
                saved = True
            elif isinstance(res, dict):
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(res, f, ensure_ascii=False, indent=2)
                saved = True
        except Exception as e:
            print(f"⚠️ Could not save result {i} via save_to_json: {e}")

        # If not saved, try to serialize the object naively
        if not saved:
            try:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(res, f, ensure_ascii=False, default=str, indent=2)
                saved = True
            except Exception as e:
                print(f"⚠️ Could not serialize result {i} to JSON: {e}")

        # Load JSON for uniform downstream parsing
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            print(f"❌ JSON file not found for result {i}; skipping.")
            continue

        table_data, summary = create_table_and_summary_with_ai(data, i, analyzer)
        if isinstance(table_data, pd.DataFrame):
            all_tables.append(table_data)
        all_summaries.append(summary)

    return all_tables, all_summaries


def print_enhanced_summary(summaries: List[Dict[str, Any]]) -> None:
    print("\n" + "=" * 70)
    print("🤖 AI-ENHANCED CHART ANALYSIS SUMMARY")
    print("=" * 70)

    for summary in summaries:
        print(f"\n📊 Result {summary.get('result_index', 'N/A')}:")
        print(f"  • Rows: {summary.get('total_rows', 'N/A')}")
        print(f"  • Columns: {summary.get('total_columns', 'N/A')}")
        if summary.get('key_insights'):
            print("  • Numeric Insights:")
            for ins in summary['key_insights']:
                try:
                    print(f"    - {ins['column']}: min={ins['min']} max={ins['max']} mean={ins['mean']:.2f} total={ins['total']:.2f}")
                except Exception:
                    print(f"    - {ins}")
        if summary.get('ai_insights'):
            print("  🧠 AI Analysis:")
            for line in str(summary['ai_insights']).splitlines():
                if line.strip():
                    print(f"    {line}")
        print("-" * 40)


# ===========================
# CLI / Main
# ===========================
def prompt_image_path() -> Optional[str]:
    print("\n📁 Provide the chart image path (or press Enter to use the default).")
    default_path = r"C:\Users\kumamay1\OneDrive - acuitykp\Work\ChartModel\Paddle\Sample_Image2.png"
    p = input(f"Path [{default_path}]: ").strip()
    if not p:
        p = default_path
    p = p.strip('"').strip("'")
    if os.path.exists(p):
        return p
    print("❌ File not found. Please re-run and provide a valid path.")
    return None


def main():
    print("🔥 AI-Enhanced Chart Analyzer (PaddleX → JSON → Table → Nova Lite) 🔥")
    print("=" * 80)

    img_path = prompt_image_path()
    if not img_path:
        return

    try:
        print(f"\n🔄 Loading PaddleX model...")
        model = create_model("PP-Chart2Table", device="cpu")

        print(f"🔍 Analyzing image: {img_path}")
        results = model.predict(input={"image": img_path}, batch_size=1)

        print("🤝 Initializing AI analyzer (Bedrock/Nova Lite)...")
        analyzer = ChartAnalyzerWithBedrock(region_name='eu-west-1')

        print("🧪 Processing results → JSON → Structured → AI insights...")
        tables, summaries = process_chart_results_with_ai(results, analyzer)

        print_enhanced_summary(summaries)

        # Save enhanced summary JSON
        os.makedirs("./output", exist_ok=True)
        with open('./output/ai_enhanced_summary.json', 'w', encoding='utf-8') as f:
            json.dump(summaries, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n💾 Summary saved: ./output/ai_enhanced_summary.json")

        # If multiple tables, also save a combined CSV
        valid_tables = [t for t in tables if isinstance(t, pd.DataFrame) and not t.empty]
        if len(valid_tables) > 1:
            combined = pd.concat(valid_tables, ignore_index=True)
            combined.to_csv('./output/combined_table.csv', index=False)
            print("📄 Combined table saved to: ./output/combined_table.csv")

        print("\n✅ Done!")

    except Exception as e:
        print(f"❌ Error during processing: {str(e)}")
        print("Please verify PaddleX is installed, the image path is valid, and try again.")


if __name__ == "__main__":
    main()