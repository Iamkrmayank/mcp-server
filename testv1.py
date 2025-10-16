# chart_to_ai_summary.py
# End-to-end: PaddleX → JSON → DataFrame/CSV → Bedrock Nova Lite summary

import os
import json
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from paddlex import create_model
import boto3
from botocore.exceptions import ClientError


# ===========================
# Bedrock (Nova Lite) Client
# ===========================
class ChartAnalyzerWithBedrock:
    def __init__(self, region_name: str = "eu-west-1"):
        self.region_name = region_name
        try:
            self.bedrock = boto3.client("bedrock-runtime", region_name=region_name)
            print(f"✅ AWS Bedrock initialized in region: {region_name}")
        except Exception as e:
            print(f"❌ Failed to initialize Bedrock: {e}")
            self.bedrock = None

    def get_ai_summary(self, table_df: pd.DataFrame, chart_context: str, raw_json: Optional[str]) -> str:
        """Generate a friendly natural-language summary using Nova Lite."""
        if not self.bedrock:
            return "AI summary unavailable – Bedrock not initialized."

        # Build prompt without nested f-strings (prevents backslash-in-expression error)
        csv_preview = ""
        try:
            csv_preview = table_df.to_csv(index=False)
        except Exception:
            pass

        parts = []
        parts.append("You are an expert data analyst. Summarize the dataset in simple natural language.")
        if chart_context:
            parts.append(f"Context: {chart_context}")
        parts.append("Below is the dataset extracted from a chart (CSV):")
        parts.append(csv_preview)
        if raw_json:
            parts.append("Raw JSON from chart-to-table (for your reference):")
            parts.append(raw_json)
        parts.append(
            "Please provide:\n"
            "1) What the dataset represents (if inferable)\n"
            "2) Key trends and patterns\n"
            "3) Highest and lowest categories with values\n"
            "4) Any notable outliers or observations\n"
            "Keep it clear and concise (4–6 sentences)."
        )
        prompt = "\n\n".join(parts)

        try:
            resp = self.bedrock.converse(
                modelId="eu.amazon.nova-lite-v1:0",
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={"maxTokens": 500, "temperature": 0.7, "topP": 0.9},
            )
            out = resp.get("output", {})
            msg = out.get("message", {})
            content = msg.get("content", [])
            if content and isinstance(content, list) and "text" in content[0]:
                return content[0]["text"]
            return json.dumps(resp, ensure_ascii=False)[:1000]
        except ClientError as e:
            return f"Error getting AI summary: {e}"
        except Exception as e:
            return f"Unexpected error: {e}"


# ===========================
# Parsing helpers
# ===========================
def parse_pipe_table(text: str) -> Optional[pd.DataFrame]:
    """Parse a simple '|' delimited table string into a DataFrame."""
    if not isinstance(text, str):
        return None
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if len(lines) < 2:
        return None

    rows: List[List[str]] = []
    for line in lines:
        parts = [p.strip() for p in line.split("|")]
        if parts and parts[0] == "":
            parts = parts[1:]
        if parts and parts[-1] == "":
            parts = parts[:-1]
        rows.append(parts)

    header = rows[0]
    data_rows = rows[1:]
    fixed = []
    for r in data_rows:
        if len(r) < len(header):
            r = r + [""] * (len(header) - len(r))
        elif len(r) > len(header):
            r = r[:len(header)]
        fixed.append(r)

    df = pd.DataFrame(fixed, columns=header)

    # Coerce numeric-looking columns (strip % then to_numeric with 'coerce' to avoid FutureWarning)
    for col in df.columns:
        if df[col].dtype == "object":
            s = df[col].astype(str).str.replace("%", "", regex=False)
            df[col] = pd.to_numeric(s, errors="coerce")
    return df


def flatten_json(json_obj: Any, parent_key: str = "", sep: str = "_") -> Dict[str, Any]:
    """Flatten nested JSON (dicts/lists of dicts) into a single dict."""
    items: List[Tuple[str, Any]] = []
    if isinstance(json_obj, dict):
        for k, v in json_obj.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_json(v, new_key, sep=sep).items())
            elif isinstance(v, list) and v and isinstance(v[0], dict):
                for i, item in enumerate(v):
                    items.extend(flatten_json(item, f"{new_key}{sep}{i}", sep=sep).items())
            else:
                items.append((new_key, v))
    return dict(items)


def dataframe_from_chart_json(data: Any) -> Optional[pd.DataFrame]:
    """
    Try multiple shapes:
      1) {"result": "<pipe table string>"}
      2) {"table": [...]}
      3) {"data": [...] or {...}}
      4) [...] (list of dicts)
      5) fallback: flatten dict
    """
    # Case 1: your earlier PP-Chart2Table JSON
    if isinstance(data, dict) and isinstance(data.get("result"), str):
        df = parse_pipe_table(data["result"])
        if df is not None:
            return df

    # Case 2: 'table'
    if isinstance(data, dict) and "table" in data:
        try:
            return pd.DataFrame(data["table"])
        except Exception:
            pass

    # Case 3: 'data'
    if isinstance(data, dict) and "data" in data:
        if isinstance(data["data"], list):
            try:
                return pd.DataFrame(data["data"])
            except Exception:
                pass
        elif isinstance(data["data"], dict):
            try:
                return pd.DataFrame([data["data"]])
            except Exception:
                pass

    # Case 4: list of dicts
    if isinstance(data, list):
        try:
            return pd.DataFrame(data)
        except Exception:
            pass

    # Case 5: flatten arbitrary dict
    if isinstance(data, dict):
        flat = flatten_json(data)
        if flat:
            try:
                return pd.DataFrame([flat])
            except Exception:
                pass

    return None


def generate_numeric_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Safe numeric summary (prevents 'method' objects, enforces float)."""
    summary = {
        "total_rows": int(len(df)),
        "total_columns": int(len(df.columns)),
        "columns": [str(c) for c in df.columns],
        "key_insights": [],
    }

    numeric_cols = df.select_dtypes(include=["number"]).columns
    for col in numeric_cols:
        col_series = pd.to_numeric(df[col], errors="coerce")
        summary["key_insights"].append({
            "column": str(col),
            "min": float((col_series.min(skipna=True) if col_series.notna().any() else 0) or 0),
            "max": float((col_series.max(skipna=True) if col_series.notna().any() else 0) or 0),
            "mean": float((col_series.mean(skipna=True) if col_series.notna().any() else 0) or 0),
            "total": float((col_series.sum(skipna=True) if col_series.notna().any() else 0) or 0),
        })
    return summary


# ===========================
# Pipeline
# ===========================
def process_chart_results_with_ai(results: Any, analyzer: ChartAnalyzerWithBedrock) -> List[Dict[str, Any]]:
    """Save each PaddleX result to JSON, parse to DataFrame, save CSV, ask Nova to summarize."""
    os.makedirs("./output", exist_ok=True)
    all_summaries: List[Dict[str, Any]] = []

    # Normalize results into an iterable
    if not isinstance(results, (list, tuple)):
        results = [results]

    for i, res in enumerate(results):
        print(f"\n---- Processing Result {i} ----")
        json_path = f"./output/res_{i}.json"

        # Persist raw output
        saved = False
        try:
            if hasattr(res, "save_to_json"):
                res.save_to_json(json_path)
                saved = True
        except Exception as e:
            print(f"⚠️ save_to_json failed for result {i}: {e}")

        if not saved:
            try:
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(res, f, ensure_ascii=False, indent=2, default=str)
                saved = True
            except Exception as e:
                print(f"⚠️ Could not serialize result {i} to JSON: {e}")

        if not os.path.exists(json_path):
            print(f"❌ Skipping result {i}: no JSON saved.")
            continue

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        raw_json_snippet = None
        try:
            raw_json_snippet = json.dumps(data, ensure_ascii=False)[:4000]
        except Exception:
            pass

        # Build DataFrame from JSON
        df = dataframe_from_chart_json(data)
        if df is None or df.empty:
            print(f"⚠️ Could not construct table for result {i}")
            all_summaries.append({"result_index": i, "ai_summary": "No table parsed from JSON."})
            continue

        # Coerce percent-like strings again just in case
        for c in df.columns:
            if df[c].dtype == "object":
                s = df[c].astype(str).str.replace("%", "", regex=False)
                df[c] = pd.to_numeric(s, errors="ignore")

        # Save CSV and print preview
        csv_path = f"./output/table_{i}.csv"
        df.to_csv(csv_path, index=False)
        print(f"📄 Table saved to: {csv_path}")
        try:
            print(f"\n=== STRUCTURED TABLE {i} ===")
            print(df.to_string(index=False))
        except Exception:
            print(df.head())

        # Local numeric summary (for your logs / JSON)
        numeric_summary = generate_numeric_summary(df)

        # AI natural-language summary
        print("🧠 Generating AI summary...")
        ai_text = analyzer.get_ai_summary(
            table_df=df,
            chart_context=f"Chart analysis result {i}",
            raw_json=raw_json_snippet,
        )

        one = {"result_index": i, **numeric_summary, "ai_summary": ai_text}
        all_summaries.append(one)

    # Persist combined summary
    with open("./output/ai_enhanced_summary.json", "w", encoding="utf-8") as f:
        json.dump(all_summaries, f, indent=2, ensure_ascii=False)
    print("\n💾 Saved: ./output/ai_enhanced_summary.json")
    return all_summaries


def prompt_image_path() -> Optional[str]:
    print("\n📁 Provide the chart image path (or press Enter to use default).")
    default_path = r"C:\Users\kumamay1\OneDrive - acuitykp\Work\ChartModel\Paddle\Sample_Image2.png"
    p = input(f"Path [{default_path}]: ").strip()
    if not p:
        p = default_path
    p = p.strip('"').strip("'")
    if os.path.exists(p):
        return p
    print("❌ File not found.")
    return None


def main():
    print("🔥 Chart → JSON → Table → Nova Summary 🔥")
    img_path = prompt_image_path()
    if not img_path:
        return

    print("🔧 Loading PaddleX model...")
    model = create_model("PP-Chart2Table", device="cpu")

    print(f"🔍 Analyzing: {img_path}")
    results = model.predict(input={"image": img_path}, batch_size=1)

    analyzer = ChartAnalyzerWithBedrock(region_name="eu-west-1")
    process_chart_results_with_ai(results, analyzer)
    print("\n✅ Done! Check ./output for JSON, CSV, and AI summary.")


if __name__ == "__main__":
    main()