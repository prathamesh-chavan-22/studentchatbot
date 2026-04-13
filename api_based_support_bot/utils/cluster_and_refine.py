import os
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from groq import Groq
from dotenv import load_dotenv
from loguru import logger
import time

def refine():
    load_dotenv()
    
    # Load data
    file_path = "grievances.csv"
    if not os.path.exists(file_path):
        logger.error(f"File {file_path} not found")
        return
    
    df = pd.read_csv(file_path)
    logger.info(f"Loaded {len(df)} grievances")
    
    # 1. Embedding
    model_name = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")
    logger.info(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    
    logger.info("Computing embeddings...")
    embeddings = model.encode(df['Grievance'].tolist(), show_progress_bar=True)
    
    # 2. Clustering
    n_clusters = 100  # Aim for a minimal but comprehensive dataset
    logger.info(f"Clustering into {n_clusters} groups...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
    df['cluster'] = kmeans.fit_predict(embeddings)
    
    # 3. LLM Refinement via Groq
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.error("GROQ_API_KEY not found in .env")
        return
    
    client = Groq(api_key=api_key)
    # Standard Groq model for high performance
    groq_model = "llama-3.3-70b-versatile"
    
    refined_qas = []
    
    for i in range(n_clusters):
        cluster_data = df[df['cluster'] == i]
        logger.info(f"Processing cluster {i+1}/{n_clusters} ({len(cluster_data)} items)")
        
        # Sample items for the prompt (limit to 10 to keep context manageable)
        # Use more diverse samples if the cluster is large
        samples = cluster_data.sample(min(12, len(cluster_data)))
        
        prompt_content = ""
        for idx, row in samples.iterrows():
            prompt_content += f"Grievance: {row['Grievance']}\nResolution: {row['RepliedGrievance']}\n---\n"
            
        system_prompt = """
        You are a helpful assistant specialized in student admission grievances (FYJC).
        Your task is to take a set of similar student grievances (in English, Marathi, or Hindi) 
        and their corresponding resolutions, and synthesize them into ONE high-quality, clear, 
        and comprehensive Question/Answer pair that addresses the core issue of this cluster.
        
        The output must be professional, accurate, and concise.
        - If the cluster has Marathi messages, the output MUST be in Marathi or bilingual (English & Marathi).
        - If the messages are in English, the output should be in English.
        
        Format the output exactly as:
        Q: [Refined Question]
        A: [Refined Answer]
        """
        
        user_prompt = f"Combine the following similar grievances into a single representative Q&A:\n\n{prompt_content}"
        
        try:
            response = client.chat.completions.create(
                model=groq_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=600
            )
            
            refined_text = response.choices[0].message.content.strip()
            # Basic validation of format
            if "Q:" in refined_text and "A:" in refined_text:
                refined_qas.append(refined_text)
                logger.success(f"Cluster {i+1} refined")
            else:
                logger.warning(f"Cluster {i+1} returned poorly formatted text: {refined_text[:100]}...")
            
            # Groq can handle high RPS, but let's be gentle
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error refining cluster {i}: {e}")
            time.sleep(3) # Wait on error
            
    # 4. Save results
    output_file = "refined_grievances.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n\n---\n\n".join(refined_qas))
    
    logger.success(f"Final refined dataset of {len(refined_qas)} QA pairs saved to {output_file}")

if __name__ == "__main__":
    refine()
