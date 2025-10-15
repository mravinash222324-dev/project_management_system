import google.generativeai as genai
#from sentence_transformers import SentenceTransformer, util
from django.conf import settings
import whisper
import re
import numpy as np
import torch

# Create a global instance of the analyzer
analyzer = None

class ProjectAnalyzer:
    def __init__(self):
        # Configure the Gemini API (FOR ALL LOGIC)
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.llm_model = genai.GenerativeModel("gemini-2.0-flash") 

        # LOCAL EMBEDDING MODEL: Retained only to satisfy model field but not used for comparison
        #self.embedding_model = SentenceTransformer('all-mpnet-base-v2')  
        
    def get_embedding(self, text):
        """Generates a vector embedding using the local SBERT model (Free)."""
        # Returns a Python list.
        return self.embedding_model.encode(text, convert_to_tensor=True).tolist()

    def check_plagiarism_and_suggest_features(self, title, abstract, existing_submissions):
        """
        AI Gatekeeper: Performs semantic similarity check and reliably identifies the most similar project using an index.
        """
        highest_similarity = 0.0
        most_similar_project = None

        if existing_submissions:
            # Create a numbered list of abstracts for the AI to reference
            numbered_abstracts = ""
            for i, sub in enumerate(existing_submissions):
                numbered_abstracts += f"{i}: \"{sub['abstract_text']}\"\n---\n"

            similarity_prompt = f"""
            You are a semantic analysis engine. A new project idea has been submitted.

            **NEW IDEA:** "{abstract}"

            **ARCHIVED IDEAS (Numbered List):**
            {numbered_abstracts}

            Your tasks are:
            1. Calculate the conceptual similarity score between the NEW IDEA and EACH of the ARCHIVED IDEAS.
            2. Identify the single project from the numbered list that is MOST similar.

            Respond with two things on a single line, separated by a pipe:
            1. The single highest similarity SCORE you found (e.g., 0.92).
            2. The INDEX number of the most similar abstract from the list above.

            Format your response EXACTLY like this: SCORE: [highest_score] | INDEX: [number]
            """
            
            try:
                response = self.llm_model.generate_content(similarity_prompt)
                
                # Robust parsing for the new format
                score_match = re.search(r"SCORE:\s*(\d+\.\d+)", response.text)
                index_match = re.search(r"INDEX:\s*(\d+)", response.text)

                if score_match:
                    highest_similarity = float(score_match.group(1))
                
                if index_match:
                    similar_project_index = int(index_match.group(1))
                    # Use the index to reliably get the project details
                    if 0 <= similar_project_index < len(existing_submissions):
                        similar_sub = existing_submissions[similar_project_index]
                        most_similar_project = {
                            'title': similar_sub['title'],
                            'student': similar_sub['student__username'],
                            'abstract_text': similar_sub['abstract_text']
                        }

            except Exception as e:
                print(f"Error during AI similarity check: {e}")
                highest_similarity = 0.0
                most_similar_project = None

        # Step 2: Proceed with scoring and suggestion logic
        if highest_similarity > 0.60:
            originality_status = "BLOCKED_HIGH_SIMILARITY"
            suggestion_prompt = f"The project '{title}' is **too similar** to existing college projects (Similarity Score: {highest_similarity:.2f}). Generate 5-6 new, unique features or architectural pivots to fully differentiate this project and make it original."
        else:
            originality_status = "ORIGINAL_PASSED"
            suggestion_prompt = f"The project idea '{title}' is original. Generate 5 suggestions for **non-essential, advanced features** to enhance its innovation and scope."
            
        analysis_prompt = f"""
        You are a college professor analyzing a project idea. Provide scores and the final analysis.
        Project Title: {title}
        Abstract: {abstract}
        Originality Check: {originality_status}. Similarity Score: {highest_similarity:.2f}
        
        Based on the above context, provide the final analysis:
        
        1. **SCORES (Rate 1-10):**
           - Relevance: [Score]
           - Feasibility: [Score]
           - Innovation: [Score]
           
        2. **SUGGESTIONS:** {suggestion_prompt}
        
        Note: If any score is 0.0, the analysis must state why.
        """
        
        try:
            final_response = self.llm_model.generate_content(analysis_prompt)
            final_text = final_response.text.strip()
            
            relevance_match = re.search(r"[Rr]elevance.*:\s*(\d+(\.\d+)?)", final_text)
            feasibility_match = re.search(r"[Ff]easibility.*:\s*(\d+(\.\d+)?)", final_text)
            innovation_match = re.search(r"[Ii]nnovation.*:\s*(\d+(\.\d+)?)", final_text)
            
            return {
                "originality_status": originality_status,
                "similarity_score": highest_similarity,
                "relevance": float(relevance_match.group(1)) if relevance_match else 0.0,
                "feasibility": float(feasibility_match.group(1)) if feasibility_match else 0.0,
                "innovation": float(innovation_match.group(1)) if innovation_match else 0.0,
                "full_report": final_text,
                "most_similar_project": most_similar_project
            }
        except Exception as e:
            return {
                "originality_status": "API_FAIL",
                "similarity_score": highest_similarity,
                "relevance": 0.0, "feasibility": 0.0, "innovation": 0.0,
                "full_report": f"AI analysis failed during final scoring. Error: {e}",
                "most_similar_project": most_similar_project
            }


    def transcribe_audio(self, audio_file_path):
        """Transcribes an audio file into text using the local Whisper model."""
        try:
            whisper_model = whisper.load_model("tiny")
            result = whisper_model.transcribe(audio_file_path)
            return result["text"]
        except Exception as e:
            print(f"Error during audio transcription: {e}")
            return None

    def find_similar_ideas(self, new_embedding, existing_embeddings, threshold=0.85):
        """Compares a new idea to existing ones using embeddings (still available if needed)."""
        similarities = util.cos_sim(new_embedding, existing_embeddings)[0]
        duplicate_indices = [i for i, score in enumerate(similarities) if score > threshold]
        return duplicate_indices

    def get_chat_response(self, prompt, conversation_history=""):
        """Generates a chat response using the Gemini API."""
        try:
            chat_session = self.llm_model.start_chat(history=[])
            response = chat_session.send_message(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error during Gemini API call: {e}")
            return "Sorry, I am unable to answer that right now."

    def analyze_idea(self, title, abstract):
        """Analyzes an idea using the Gemini API."""
        prompt = f"""
        Analyze the following project idea for a college project.
        Title: {title}
        Abstract: {abstract}
        
        Provide a detailed analysis including:
        - Relevance (1-10)
        - Feasibility (1-10)
        - Innovation (1-10)
        """
        try:
            response = self.llm_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error during Gemini API call: {e}")
            return "Failed to analyze the project."

    def generate_viva_questions(self, title, abstract, progress_percentage):
        """
        Generates conditional viva questions based on project progress.
        """
        # --- Conditional Logic to determine review stage ---
        if progress_percentage < 30:
            stage = "Initial Design & Concepts (Focus on Feasibility)"
            focus = "fundamental concepts, required algorithms, and high-level design choices."
        elif progress_percentage < 80:
            stage = "Mid-Review & Implementation (Focus on Progress)"
            focus = "current implementation status, architectural decisions, and unexpected problems encountered so far."
        else:
            # 80% or higher is the final technical review
            stage = "Final Examination (Code Deep Dive & Optimization)"
            focus = "specific technical details of the code, optimization techniques, scalability, and deployment strategy."

        prompt = f"""
        You are a highly demanding project examiner for a {stage} review. Your task is to generate 5 challenging viva questions.
        
        Project Title: {title}
        Project Abstract: {abstract}
        Project Progress: {progress_percentage}% Complete.
        
        The questions must specifically focus on the {focus}. Do not include the preamble in your response.
        
        Generate the list of questions, with each question numbered 1 to 5.
        """
        try:
            chat_session = self.llm_model.start_chat(history=[])
            response = chat_session.send_message(prompt)
            
            questions_text = response.text.strip()
            
            # Use regex to find all the numbered questions in the response
            questions = re.findall(r'(\d+\.\s*.*)', questions_text)

            return [q.strip() for q in questions if q.strip()]
        except Exception as e:
            print(f"Error during Gemini API call: {e}")
            return ["Failed to generate viva questions."]

    def evaluate_viva_answer(self, question, answer, abstract):
        """Evaluates a student's viva answer using Gemini API."""
        if answer.strip() == question.strip():
            return {"score": "0/10", "feedback": "Your answer is just the question repeated."}

        prompt = f"""
        Project Abstract: {abstract}
        Question: {question}
        Answer: {answer}

        Evaluate the answer (Score out of 10) and give feedback:
        """
        try:
            response = self.llm_model.generate_content(prompt)
            evaluation_text = response.text.strip()
            score_match = re.search(r"Score:\s*(\d+(\.\d+)?)\s*/10", evaluation_text)
            feedback_match = re.search(r"Feedback:([\s\S]*)", evaluation_text)

            score = score_match.group(1).strip() if score_match else 'N/A'
            feedback = feedback_match.group(1).strip().strip('**') if feedback_match else 'No feedback provided.'
            
            return {"score": score, "feedback": feedback}
        except Exception as e:
            print(f"Error during Gemini API call: {e}")
            return {"score": "N/A", "feedback": "Failed to evaluate the answer."}

# Create a single instance
analyzer = ProjectAnalyzer()


