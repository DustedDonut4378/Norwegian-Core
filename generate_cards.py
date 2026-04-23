import os
import time
import json
import datetime
import concurrent.futures
import google.generativeai as genai

# ANSI Colors for a better CLI experience
class Colors:
    HEADER = '\033[95m'
    PRO = '\033[94m'      # Blue for Pro
    FLASH = '\033[93m'    # Yellow for Flash
    SUCCESS = '\033[92m'  # Green
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# Setup
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(PROJECT_DIR, "Input")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "Output")
INFO_FILE = os.path.join(PROJECT_DIR, "info.md")
PROGRESS_FILE = os.path.join(OUTPUT_DIR, "progress.json")

# Model Names
PRO_MODEL = 'gemini-3.1-pro-preview'
FLASH_MODEL = 'gemini-3-flash-preview'

# Quota
PRO_DAILY_LIMIT = 250
RATE_LIMIT_DELAY = 1  # Seconds between Pro requests

# Load API Key
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(PROJECT_DIR, ".env"))
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env")
    genai.configure(api_key=api_key)
except Exception as e:
    print(f"{Colors.FAIL}Error loading API Key from .env: {e}{Colors.ENDC}")
    exit(1)

def call_model(model_name, system_instr, prompt, is_json=False, max_retries=2, label=None):
    for attempt in range(max_retries):
        try:
            model = genai.GenerativeModel(model_name=model_name, system_instruction=system_instr)
            config = genai.types.GenerationConfig(response_mime_type="application/json") if is_json else None
            response = model.generate_content(prompt, generation_config=config)
            return response.text.strip()
        except Exception as e:
            if attempt < max_retries - 1:
                msg = f"({label}) " if label else ""
                print(f"\n{Colors.WARNING}  ⚠️ {msg}Model failed. Retrying in 10s...{Colors.ENDC}")
                time.sleep(10)
            else:
                raise Exception(f"Model {model_name} failed after {max_retries} attempts: {e}")

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"date": str(datetime.date.today()), "pro_count": 0, "files": {}}

def save_progress(progress):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=4)

def print_banner(progress):
    os.system('clear' if os.name == 'posix' else 'cls')
    print(f"{Colors.HEADER}{Colors.BOLD}=================================================={Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}       KELLY NORWEGIAN - CONSENSUS WORKFLOW       {Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}=================================================={Colors.ENDC}")
    print(f"Date: {progress['date']} | Daily Quota: {Colors.PRO}{progress['pro_count']}/{PRO_DAILY_LIMIT}{Colors.ENDC}")
    print(f"--------------------------------------------------\n")

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    progress = load_progress()
    today = str(datetime.date.today())
    
    if progress["date"] != today:
        progress["date"] = today
        progress["pro_count"] = 0
        save_progress(progress)

    print_banner(progress)

    files = sorted([f for f in os.listdir(INPUT_DIR) if f.endswith('.csv')])
    if not files:
        print(f"{Colors.FAIL}No CSV files found in {INPUT_DIR}{Colors.ENDC}")
        return

    print(f"{Colors.BOLD}Available Files:{Colors.ENDC}")
    for i, f in enumerate(files):
        status = f" {Colors.WARNING}(In Progress: {progress['files'].get(f, 0)} batches){Colors.ENDC}" if f in progress["files"] else ""
        print(f"  [{i}] {f}{status}")
    
    try:
        choice_input = input(f"\n{Colors.BOLD}Select file index (or 'q' to quit): {Colors.ENDC}")
        if choice_input.lower() == 'q': return
        filename = files[int(choice_input)]
    except:
        print(f"\n{Colors.FAIL}Invalid selection.{Colors.ENDC}")
        return

    # Select CEFR Level
    levels = ['A1', 'A2', 'B1']
    print(f"\n{Colors.BOLD}Select CEFR Level:{Colors.ENDC}")
    for i, lvl in enumerate(levels):
        print(f"  [{i}] {lvl}")
    
    cefr_choice = None
    while cefr_choice is None:
        try:
            cefr_choice_idx = input(f"\n{Colors.BOLD}Select level index: {Colors.ENDC}").strip()
            if not cefr_choice_idx:
                continue
            idx = int(cefr_choice_idx)
            if 0 <= idx < len(levels):
                cefr_choice = levels[idx]
            else:
                print(f"{Colors.FAIL}Index out of range. Please try again.{Colors.ENDC}")
        except ValueError:
            print(f"{Colors.FAIL}Invalid input. Please enter a valid index.{Colors.ENDC}")
        except (EOFError, KeyboardInterrupt):
            print(f"\n{Colors.WARNING}Exiting...{Colors.ENDC}")
            return
    
    rules_path = os.path.join(PROJECT_DIR, cefr_choice)

    input_path = os.path.join(INPUT_DIR, filename)
    with open(input_path, 'r') as f:
        input_lines = [line.strip() for line in f if line.strip()]
    
    output_file = os.path.join(OUTPUT_DIR, f"processed_{filename}")

    # Create a dedicated directory for individual batch files
    file_base = os.path.splitext(filename)[0]
    part_dir = os.path.join(OUTPUT_DIR, file_base)
    if not os.path.exists(part_dir):
        os.makedirs(part_dir)

    start_batch = progress["files"].get(filename, 0)
    # Check for output file consistency
    if start_batch > 0 and not os.path.exists(output_file):
        print(f"{Colors.WARNING}⚠️ Output file missing. Resetting progress to start.{Colors.ENDC}")
        start_batch = 0
        progress["files"][filename] = 0
        save_progress(progress)
    
    # Dynamic messaging
    if start_batch == 0:
        print(f"\n{Colors.SUCCESS}🚀 Starting {filename} [{cefr_choice}]...{Colors.ENDC}")
    else:
        print(f"\n{Colors.SUCCESS}🚀 Resuming {filename} [{cefr_choice}] from batch {start_batch + 1}...{Colors.ENDC}")

    # Load Instructions
    try:
        with open(os.path.join(rules_path, 'Generation_Rules.md'), 'r') as f: gen_instr = f.read()
        with open(os.path.join(rules_path, 'Fact_Checking_Rules.md'), 'r') as f: crit_instr = f.read()
        with open(os.path.join(rules_path, 'Final_Consensus.md'), 'r') as f: cons_instr = f.read()
    except Exception as e:
        print(f"{Colors.FAIL}Error loading markdown rules from {rules_path}: {e}{Colors.ENDC}")
        return

    try:
        for i in range(start_batch * 10, len(input_lines), 10):
            batch_idx = i // 10
            batch = input_lines[i:i+10]
            
            print(f"\n{Colors.BOLD}--- Batch {batch_idx + 1} | Usage: {progress['pro_count']}/{PRO_DAILY_LIMIT} ---{Colors.ENDC}")
            
            # Step 1: Generation
            print(f"  Initial Generation...", end="", flush=True)
            original_output = call_model(PRO_MODEL, gen_instr, "\n".join(batch), label="Generation")
            progress["pro_count"] += 1
            print(f" {Colors.SUCCESS}Done{Colors.ENDC}")
            time.sleep(RATE_LIMIT_DELAY)
            
            # Steps 2-4: Parallel Critiques
            print(f"  Parallel Critiques:")
            def tracked_call(name, model, instr, data, is_json):
                res = call_model(model, instr, data, is_json=is_json, label=name)
                print(f"    - {Colors.SUCCESS}{name} done{Colors.ENDC}")
                return res

            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                f_a = executor.submit(tracked_call, "Critique A", PRO_MODEL, crit_instr, original_output, True)
                f_b = executor.submit(tracked_call, "Critique B", PRO_MODEL, crit_instr, original_output, True)
                f_c = executor.submit(tracked_call, "Critique C", PRO_MODEL, crit_instr, original_output, True)
                
                try:
                    critique_a = f_a.result()
                    critique_b = f_b.result()
                    critique_c = f_c.result()
                except Exception as e:
                    print(f" {Colors.FAIL}Batch failed during critiques: {e}{Colors.ENDC}")
                    break
            
            progress["pro_count"] += 3 
            time.sleep(RATE_LIMIT_DELAY)
            
            # Step 5: Final Consensus
            print(f"  Final Consensus...", end="", flush=True)
            consensus_prompt = f"Original Output:\n{original_output}\n\nCritique A (Pro):\n{critique_a}\n\nCritique B (Pro):\n{critique_b}\n\nCritique C (Pro):\n{critique_c}"
            
            final_output = ""
            success = False
            for consensus_attempt in range(3):
                try:
                    final_output = call_model(PRO_MODEL, cons_instr, consensus_prompt, label=f"Consensus Try {consensus_attempt+1}")
                    progress["pro_count"] += 1
                    
                    # Check for 10 non-empty lines
                    final_lines = [line.strip() for line in final_output.split('\n') if line.strip()]
                    if len(final_lines) == 10:
                        final_output = "\n".join(final_lines)
                        success = True
                        break
                    
                    if consensus_attempt < 2:
                        print(f" {Colors.WARNING}Line mismatch ({len(final_lines)}/10). Retrying...{Colors.ENDC}", end="", flush=True)
                        time.sleep(5)
                        consensus_prompt += "\n\nCRITICAL: You MUST return EXACTLY 10 lines. Do not add explanations."
                except Exception as e:
                    print(f" {Colors.WARNING}Consensus attempt failed: {e}{Colors.ENDC}")
                    time.sleep(5)
            
            if success:
                # Append to consolidated CSV
                with open(output_file, 'a') as out:
                    out.write(final_output + "\n")
                
                # Save individual batch Markdown file with full history
                batch_file_path = os.path.join(part_dir, f"batch_{batch_idx + 1:03d}.md")
                with open(batch_file_path, 'w') as bf:
                    bf.write(f"# {file_base} - Batch {batch_idx + 1}\n\n")
                    
                    bf.write("## 📥 Input Lines\n")
                    bf.write("```text\n" + "\n".join(batch) + "\n```\n\n")
                    
                    bf.write(f"## 🤖 Initial Generation ({PRO_MODEL})\n")
                    bf.write("```csv\n" + original_output + "\n```\n\n")
                    
                    bf.write("## 🔍 Critiques\n")
                    bf.write(f"### Critique A (Pro)\n```json\n{critique_a}\n```\n\n")
                    bf.write(f"### Critique B (Pro)\n```json\n{critique_b}\n```\n\n")
                    bf.write(f"### Critique C (Pro)\n```json\n{critique_c}\n```\n\n")
                    
                    bf.write(f"## 🏆 Final Consensus ({PRO_MODEL})\n")
                    bf.write("```csv\n" + final_output + "\n```\n")

                progress["files"][filename] = batch_idx + 1
                save_progress(progress)
                print(f" {Colors.SUCCESS}Done{Colors.ENDC}")
            else:
                print(f" {Colors.FAIL}Failed (Line mismatch after 3 attempts){Colors.ENDC}")
                break
            
            time.sleep(RATE_LIMIT_DELAY)

        # Final check for completion
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                processed_lines_count = sum(1 for line in f if line.strip())
            
            if processed_lines_count >= len(input_lines):
                print(f"\n{Colors.SUCCESS}{Colors.BOLD}✅ FINISHED: {filename} has been fully processed! ({processed_lines_count}/{len(input_lines)} lines){Colors.ENDC}")

            
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}🛑 Stopped by user. Progress saved.{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ Fatal Error: {e}{Colors.ENDC}")
    finally:
        save_progress(progress)
        print(f"\n{Colors.SUCCESS}Results in Output/processed_{filename}{Colors.ENDC}\n")

if __name__ == "__main__":
    main()
