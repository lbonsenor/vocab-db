from typing import Dict, List
import supabase

def getUpos(client: supabase.Client, tag: str) -> str:
    response = client.table("upos_tags").select('label').eq('id', tag).execute().data
    return response[0]['label'].capitalize()


def getXpos(client: supabase.Client, tags: List[str]) -> List[str]:
    unique_ids = list(set(tags))

    response = client.table('xpos_tags').select('id', 'label').in_('id', unique_ids).execute()
    found: Dict[str, str] = { item['id']: item['label'] for item in response.data }

    result = []
    new_entries = []

    for tag in tags:
        if tag in found:
            result.append(found[tag])
        else:
            # Prompt user
            while True:
                label = input(f"XPOS tag '{tag} not found. Please enter a label for it: ").strip()
                if label:
                    break
                print("Input cannot be empty or whitespace. Try again.")

            found[tag] = label
            result.append(label)
            new_entries.append({'id': tag, 'label': label})

    if new_entries:
        client.table('xpos_tags').insert(new_entries).execute()

    return result

def getMorphemes(client: supabase.Client, morphemes: List[str], xpos_tags: List[str]):
    results = []

    for text, xpos_tag in zip(morphemes, xpos_tags):
        response = client.table("morphemes").select("id, text, xpos_id, translation, xpos_tags(label)").eq("text", text).eq("xpos_id", xpos_tag).execute()

        if response.data:
            for row in response.data:
                results.append({'id': row["id"], 'text': row["text"], 'xpos': row["xpos_tags"]["label"], 'translation': row["translation"]})
        else:
            while True:
                translation = input(f"Morpheme '{text}' with XPOS tag '{xpos_tag}' not found. Please enter a translation for it: ").strip()
                if translation:
                    break
                print("Input cannot be empty or whitespace. Try again.")
            
            insert_response = (
                client.table("morphemes")
                .insert({
                    "text": text,
                    "xpos_id": xpos_tag,
                    "translation": translation
                }).execute()
            )
            
            if insert_response.data:
                results.append({'id': insert_response.data[0]["id"], 'text': text, 'xpos': xpos_tag, 'translation': translation})

    return results

def getTranslation(client: supabase.Client, text: str, upos_tag: str, morphemes: List):
    response = client.table("words").select("translation").eq("text", text).eq("upos_id", upos_tag).execute()

    if response.data:
        return response.data[0]['translation']
    
    else:
        while True:
            translation = input(f"Word '{text}' with UPOS tag '{upos_tag}' not found. Please enter a translation for it: ").strip()
            if translation:
                break
            print("Input cannot be empty or whitespace. Try again.")
        
        words_response = client.table("words").insert({
            "text": text,
            "upos_id": upos_tag,
            "translation": translation
        }).execute()

        if words_response.data:
            lemmas = []
            for idx, morpheme in enumerate(morphemes):
                lemmas.append({
                    "word_id": words_response.data[0]["id"],
                    "index": idx,
                    "morpheme_id": morpheme["id"]
                })
            lemmas_response = client.table("lemmas").insert(lemmas).execute()
    
    return translation