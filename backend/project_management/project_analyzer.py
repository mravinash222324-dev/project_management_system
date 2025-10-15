import google.generativeai as genai
# from sentence_transformers import SentenceTransformer, util
from django.conf import settings
# import whisper
import re
import numpy as np
# import torch

# Create a global instance of the analyzer
analyzer = None

class ProjectAnalyzer:
    def __init__(self):
        # Configure Gemini API (Main Brain)
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.llm_model = genai.GenerativeModel("gemini-2.0-flash")

        # Local embedding model (disabled on Render Free Tier)
        # self.embedding_model = SentenceTransformer('all-mpnet-base-v2')
        
    def get_embedding(self, text):
        """Placeholder for embedding (disabled to save memory)."""
        # return self.embedding_model.encode(text, convert_to_tensor=True).tolist()
        return []  # Mock empty embedding for compatibility

    def check_plagiarism_and_suggest_features(self, title, abstract, existing_submissions):
        """Uses Gemini API for similarity and originality check."""
        highest_similarity = 0.0
        most_similar_project = None

        if existing_submissions:
            numbered_abstracts = ""
            for i, sub in enumerate(existing_submissions):
                numbered_abstracts += f"{i}: \"{sub['abstract_text']}\"\n---\n"

            similarity_prompt = f"""
            You are a semantic analysis engine. A new project idea has been submitted.

            NEW IDEA: "{abstract}"

            ARCHIVED IDEAS (Numbered List):
            {numbered_abstracts}

            Your task:
            1. Find the single project that is most conceptually similar.
            2. Return only two values in one line:
               SCORE: [highest_score] | INDEX: [number]
            """

            try:
                response = self.llm_model.generate_content(similarity_prompt)
                score_match = re.search(r"SCORE:\s*(\d+\.\d+)", response.text)
                index_match = re.search(r"INDEX:\s*(\d+)", response.text)

                if score_match:
                    highest_similarity = float(score_match.group(1))

                if index_match:
                    similar_project_index = int(index_match.group(1))
                    if 0 <= similar_project_index < len(existing_submissions):
                        similar_sub = existing_submissions[similar_project_index]
                        most_similar_project = {
                            'title': similar_sub['title'],
                            'student': similar_sub['student__username'],
                            'abstract_text': similar_sub['abstract_text']
                        }

            except Exception as e:
                print(f"Error during AI similarity check: {e}")

        # Step 2 — Suggest new ideas
        if highest_similarity > 0.60:
            originality_status = "BLOCKED_HIGH_SIMILARITY"
            suggestion_prompt = (
                f"The project '{title}' is too similar (Score: {highest_similarity:.2f}). "
                "Suggest 5–6 new unique features to make it original."
            )
        else:
            originality_status = "ORIGINAL_PASSED"
            suggestion_prompt = (
                f"The project '{title}' is original. "
                "Suggest 5 advanced or innovative features to enhance it."
            )

        analysis_prompt = f"""
        You are a college professor analyzing a project idea.
        Title: {title}
        Abstract: {abstract}
        Originality: {originality_status} (Score: {highest_similarity:.2f})

        Provide:
        1. SCORES (Rate 1–10):
           - Relevance:
           - Feasibility:
           - Innovation:

        2. SUGGESTIONS: {suggestion_prompt}
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
                "full_report": f"AI analysis failed. Error: {e}",
                "most_similar_project": most_similar_project
            }

    # --- Disabled Heavy Feature ---
    # def transcribe_audio(self, audio_file_path):
    #     """Whisper model disabled for Render Free Tier."""
    #     return "Audio transcription temporarily disabled on this deployment."

    def get_chat_response(self, prompt, conversation_history=""):
        """Chat with Gemini API."""
        try:
            chat_session = self.llm_model.start_chat(history=[])
            response = chat_session.send_message(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error during Gemini API call: {e}")
            return "Sorry, I am unable to answer that right now."

    def analyze_idea(self, title, abstract):
        """Analyze project idea."""
        prompt = f"""
        Analyze the following college project idea:
        Title: {title}
        Abstract: {abstract}

        Provide Relevance, Feasibility, and Innovation scores (1–10)
        with brief reasoning.
        """
        try:
            response = self.llm_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error during Gemini API call: {e}")
            return "Failed to analyze project."

    def generate_viva_questions(self, title, abstract, progress_percentage):
        """Generate viva questions using Gemini."""
        if progress_percentage < 30:
            stage = "Initial Design & Concepts"
            focus = "fundamental concepts and design choices"
        elif progress_percentage < 80:
            stage = "Mid-Review & Implementation"
            focus = "implementation status and encountered challenges"
        else:
            stage = "Final Review"
            focus = "technical details, optimization, and deployment"

        prompt = f"""
        You are a strict examiner for {stage}.
        Project Title: {title}
        Abstract: {abstract}
        Progress: {progress_percentage}%

        Generate 5 numbered viva questions focusing on {focus}.
        """

        try:
            response = self.llm_model.generate_content(prompt)
            questions = re.findall(r'\d+\.\s*.*', response.text)
            return [q.strip() for q in questions if q.strip()]
        except Exception as e:
            print(f"Error during Gemini API call: {e}")
            return ["Failed to generate viva questions."]

    def evaluate_viva_answer(self, question, answer, abstract):
        """Evaluate viva answer with Gemini."""
        if answer.strip() == question.strip():
            return {"score": "0/10", "feedback": "Your answer is just the question repeated."}

        prompt = f"""
        Project Abstract: {abstract}
        Question: {question}
        Answer: {answer}

        Evaluate the answer (Score out of 10) and provide feedback.
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
            return {"score": "N/A", "feedback": "Failed to evaluate answer."}


# Create a single instance
analyzer = ProjectAnalyzer()
