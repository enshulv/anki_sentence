from anki.collection import Collection
from openai import OpenAI
import time
from requests.exceptions import RequestException, Timeout
import json
import os

def load_config():
    config_path = 'config.json'
    if not os.path.exists(config_path):
        config = {
            "COLLECTION_PATH": "",
            "DECK_NAME": "",
            "FIELD_NAME": "",
            "NUM_CARDS": 20,
            "NUM_SENTENCES": 5,
            "API_KEY": "",
            "BASE_URL": "https://api.deepseek.com/v1",
            "MODEL_NAME": "deepseek-chat",
            "TIMEOUT": 300,
            "MAX_RETRIES": 3,
            "RETRY_DELAY": 5,
            "SYSTEM_PROMPT": "You are a helpful assistant that generates simple example sentences for English learners. The sentences should be short, easy to understand, and clearly demonstrate the meaning of the given word. Always include the target word in the sentence.",
            "USER_PROMPT": "Generate {num_sentences} simple example sentences for the word '{word}'. Each sentence should be followed by its Chinese translation. Format the entire output as follows:\n<br><span style=\"font-size:medium\">English sentence 1. 中文翻译1。</span><br><span style=\"font-size:medium\">English sentence 2. 中文翻译2。</span><br>\n... and so on for all {num_sentences} sentences."
        }
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"配置文件已创建在 {config_path}。请填写必要信息后重新运行程序。")
        input("按下回车键以退出...")
        exit()
    
    with open(config_path, 'r',encoding='utf-8') as f:
        return json.load(f)

CONFIG = load_config()

client = OpenAI(api_key=CONFIG['API_KEY'], base_url=CONFIG['BASE_URL'])

def generate_sentences(word, num_sentences=5):
    for attempt in range(CONFIG['MAX_RETRIES']):
        try:
            response = client.chat.completions.create(
                model=CONFIG['MODEL_NAME'],
                messages=[
                    {"role": "system", "content": CONFIG['SYSTEM_PROMPT']},
                    {"role": "user", "content": CONFIG['USER_PROMPT'].format(num_sentences=num_sentences, word=word)}
                ],
                timeout=CONFIG['TIMEOUT']
            )
            return response.choices[0].message.content.strip()
        except Timeout:
            print(f"生成例句时超时 (尝试 {attempt + 1}/{CONFIG['MAX_RETRIES']})")
            if attempt < CONFIG['MAX_RETRIES'] - 1:
                print(f"等待 {CONFIG['RETRY_DELAY']} 秒后重试...")
                time.sleep(CONFIG['RETRY_DELAY'])
            else:
                raise TimeoutError(f"处理单词 '{word}' 时，API 调用连续 {CONFIG['MAX_RETRIES']} 次超时")
        except Exception as e:
            print(f"生成例句时出错 (尝试 {attempt + 1}/{CONFIG['MAX_RETRIES']}): {str(e)}")
            if attempt < CONFIG['MAX_RETRIES'] - 1:
                print(f"等待 {CONFIG['RETRY_DELAY']} 秒后重试...")
                time.sleep(CONFIG['RETRY_DELAY'])
            else:
                raise RuntimeError(f"处理单词 '{word}' 时，连续 {CONFIG['MAX_RETRIES']} 次尝试均失败") from e

def update_note(col, note, formatted_sentences):
    current_content = note[CONFIG['FIELD_NAME']]
    if '<br>' in current_content:
        parts = current_content.rsplit('<br>', 1)
        new_content = f"{parts[0]}<br>{formatted_sentences}<br>{parts[1] if len(parts) > 1 else ''}"
    else:
        new_content = f"{current_content}{formatted_sentences}"
    
    note[CONFIG['FIELD_NAME']] = new_content
    col.update_note(note)

def process_deck(collection_path, deck_name, num_cards=None, num_sentences=5):
    try:
        col = Collection(collection_path)
        print(f"成功连接到数据库: {collection_path}")
        
        deck_id = col.decks.id_for_name(deck_name)
        print(f"找到牌组 '{deck_name}' 的 ID: {deck_id}")
        
        query = f"deck:\"{deck_name}\" is:new"
        new_cards = col.find_cards(query)
        print(f"找到的新卡片总数: {len(new_cards)}")

        card_due_info = []
        for card_id in new_cards:
            card = col.get_card(card_id)
            note = card.note()
            word = note[CONFIG['FIELD_NAME']].split('<br')[0].strip()
            card_due_info.append((card_id, card.due, word))

        card_due_info.sort(key=lambda x: x[1])

        if num_cards is not None:
            card_due_info = card_due_info[:num_cards]
        
        print(f"将处理 {len(card_due_info)} 张新卡片")

        for card_id, due, word in card_due_info:
            print(f"处理单词: {word} (到期顺序: {due})")
            
            card = col.get_card(card_id)
            note = card.note()
            try:
                formatted_sentences = generate_sentences(word, num_sentences)
                update_note(col, note, formatted_sentences)
            except (TimeoutError, RuntimeError) as e:
                print(f"错误: {str(e)}")
                print("由于持续错误，程序终止。")
                break
            
            time.sleep(1)

        print(f"完成！已为{len(card_due_info)}张新卡片添加例句。")
    except Exception as e:
        print(f"处理牌组时发生错误：{str(e)}")
    finally:
        if 'col' in locals():
            col.close()

if __name__ == "__main__":
    process_deck(CONFIG['COLLECTION_PATH'], CONFIG['DECK_NAME'], CONFIG['NUM_CARDS'], CONFIG['NUM_SENTENCES'])
    input("按下回车键以退出...")
