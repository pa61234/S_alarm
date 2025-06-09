from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

tokenizer = AutoTokenizer.from_pretrained("monologg/koelectra-base-v3-discriminator")
model = AutoModelForTokenClassification.from_pretrained("monologg/koelectra-base-v3-discriminator")
ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple")

def extract_companies(text: str):
    results = ner_pipeline(text)
    companies = [r['word'] for r in results if r['entity_group'] == 'ORG']
    return list(set(companies))
