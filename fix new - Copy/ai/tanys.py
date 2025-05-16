import google.generativeai as genai

class GeminiAI:
    def __init__(self):
        genai.configure(api_key="AIzaSyBPddmxJ5KDxoqhm0FfhUUU9IWtek0dyFs")
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction="Anda adalah asisten AI bahasa Indonesia, jawab ringkas tanpa tanda baca"
        )
    
    def ask(self, prompt):
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Maaf, terjadi kesalahan: {str(e)}"