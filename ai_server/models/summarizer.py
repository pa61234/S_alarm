from transformers import pipeline

summarizer = pipeline("summarization", model="digit82/kobart-summarization")

def summarize(text: str) -> str:
    result = summarizer(text, max_length=30, min_length=10, do_sample=False)
    return result[0]['summary_text']
