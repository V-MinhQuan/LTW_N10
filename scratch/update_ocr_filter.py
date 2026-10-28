with open('QLVB/web/ai_services.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = """                        parts = candidates[0].get('content', {}).get('parts', [])
                        if parts:
                            return parts[0].get('text', '').strip()"""

replacement = """                        parts = candidates[0].get('content', {}).get('parts', [])
                        if parts:
                            raw_ocr = parts[0].get('text', '').strip()
                            cleaned_lines = []
                            for line in raw_ocr.splitlines():
                                l_low = line.strip().lower()
                                if any(l_low.startswith(pfx) for pfx in ['dưới đây là', 'đây là', 'chắc chắn rồi', 'here is', 'sau đây là']):
                                    continue
                                cleaned_lines.append(line)
                            return '\\n'.join(cleaned_lines).strip()"""

text_norm = text.replace('\r\n', '\n')
target_norm = target.replace('\r\n', '\n')
replacement_norm = replacement.replace('\r\n', '\n')

assert target_norm in text_norm, 'target not found in ai_services.py'
text_norm = text_norm.replace(target_norm, replacement_norm, 1)

with open('QLVB/web/ai_services.py', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(text_norm)
print('Updated _call_gemini_multimodal_ocr in ai_services.py!')

