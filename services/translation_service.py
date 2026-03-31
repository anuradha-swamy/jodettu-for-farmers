import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from typing import Dict, Any, List
import asyncio
from concurrent.futures import ThreadPoolExecutor

class IndicTrans2Service:
    def __init__(self):
        """Initialize IndicTrans2 translation model"""
        try:
            # Model configuration for IndicTrans2
            self.model_name = "ai4bharat/indictrans2-en-indic-1B"
            
            # Supported languages
            self.supported_languages = {
                'en': 'English',
                'hi': 'Hindi',
                'bn': 'Bengali',
                'gu': 'Gujarati',
                'kn': 'Kannada',
                'ml': 'Malayalam',
                'mr': 'Marathi',
                'or': 'Odia',
                'pa': 'Punjabi',
                'ta': 'Tamil',
                'te': 'Telugu',
                'as': 'Assamese',
                'ur': 'Urdu'
            }
            
            # Language codes for IndicTrans2
            self.indic_lang_codes = {
                'hi': 'hin',
                'bn': 'ben',
                'gu': 'guj',
                'kn': 'kan',
                'ml': 'mal',
                'mr': 'mar',
                'or': 'ori',
                'pa': 'pan',
                'ta': 'tam',
                'te': 'tel',
                'as': 'asm',
                'ur': 'urd'
            }
            
            # Initialize tokenizer and model
            print("Loading IndicTrans2 model...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            
            # Move to GPU if available
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            self.model.to(self.device)
            
            # Thread pool for async execution
            self.executor = ThreadPoolExecutor(max_workers=2)
            
            print(f"IndicTrans2 model loaded on {self.device}")
            
        except Exception as e:
            print(f"Error loading IndicTrans2 model: {e}")
            self.model = None
            self.tokenizer = None

    def _prepare_input(self, text: str, src_lang: str, tgt_lang: str) -> str:
        """Prepare input text for translation"""
        if src_lang == 'en':
            # English to Indic
            indic_code = self.indic_lang_codes.get(tgt_lang, tgt_lang)
            return f">>2{indic_code}<< {text}"
        elif tgt_lang == 'en':
            # Indic to English
            indic_code = self.indic_lang_codes.get(src_lang, src_lang)
            return f">>2en<< {text}"
        else:
            # Indic to Indic (via English as intermediate)
            return f">>2{self.indic_lang_codes.get(tgt_lang, tgt_lang)}<< {text}"

    async def translate(self, text: str, src_lang: str, tgt_lang: str) -> Dict[str, Any]:
        """
        Translate text from source language to target language
        Args:
            text: Text to translate
            src_lang: Source language code
            tgt_lang: Target language code
        Returns:
            Dictionary with translation result
        """
        if not self.model or not self.tokenizer:
            return {"error": "Translation model not loaded"}

        try:
            # Validate languages
            if src_lang not in self.supported_languages:
                return {"error": f"Source language '{src_lang}' not supported"}
            
            if tgt_lang not in self.supported_languages:
                return {"error": f"Target language '{tgt_lang}' not supported"}

            # Prepare input
            input_text = self._prepare_input(text, src_lang, tgt_lang)
            
            # Tokenize
            inputs = self.tokenizer(
                input_text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            ).to(self.device)
            
            # Generate translation
            with torch.no_grad():
                translated_tokens = self.model.generate(
                    **inputs,
                    max_length=512,
                    num_beams=5,
                    early_stopping=True,
                    do_sample=False
                )
            
            # Decode translation
            translation = self.tokenizer.decode(
                translated_tokens[0],
                skip_special_tokens=True
            )
            
            return {
                "success": True,
                "source_text": text,
                "translated_text": translation,
                "source_language": self.supported_languages[src_lang],
                "target_language": self.supported_languages[tgt_lang],
                "source_code": src_lang,
                "target_code": tgt_lang
            }
            
        except Exception as e:
            return {"error": f"Translation failed: {str(e)}"}

    async def translate_batch(self, texts: List[str], src_lang: str, tgt_lang: str) -> Dict[str, Any]:
        """
        Translate multiple texts
        Args:
            texts: List of texts to translate
            src_lang: Source language code
            tgt_lang: Target language code
        Returns:
            Dictionary with batch translation results
        """
        if not self.model or not self.tokenizer:
            return {"error": "Translation model not loaded"}

        try:
            translations = []
            
            for text in texts:
                result = await self.translate(text, src_lang, tgt_lang)
                translations.append(result)
            
            successful_translations = [t for t in translations if t.get("success")]
            failed_translations = [t for t in translations if not t.get("success")]
            
            return {
                "success": len(successful_translations) > 0,
                "translations": translations,
                "total_count": len(texts),
                "successful_count": len(successful_translations),
                "failed_count": len(failed_translations)
            }
            
        except Exception as e:
            return {"error": f"Batch translation failed: {str(e)}"}

    async def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Simple language detection based on character patterns
        Args:
            text: Text to analyze
        Returns:
            Dictionary with detected language
        """
        try:
            # Simple heuristic-based language detection
            text_sample = text[:100]  # Use first 100 characters
            
            # Check for Devanagari script (Hindi, Marathi, Nepali, etc.)
            devanagari_range = range(0x0900, 0x097F)
            devanagari_chars = sum(1 for char in text_sample if ord(char) in devanagari_range)
            
            # Check for Bengali script
            bengali_range = range(0x0980, 0x09FF)
            bengali_chars = sum(1 for char in text_sample if ord(char) in bengali_range)
            
            # Check for Gujarati script
            gujarati_range = range(0x0A80, 0x0AFF)
            gujarati_chars = sum(1 for char in text_sample if ord(char) in gujarati_range)
            
            # Check for Gurmukhi script (Punjabi)
            gurmukhi_range = range(0x0A00, 0x0A7F)
            gurmukhi_chars = sum(1 for char in text_sample if ord(char) in gurmukhi_range)
            
            # Check for Tamil script
            tamil_range = range(0x0B80, 0x0BFF)
            tamil_chars = sum(1 for char in text_sample if ord(char) in tamil_range)
            
            # Check for Telugu script
            telugu_range = range(0x0C00, 0x0C7F)
            telugu_chars = sum(1 for char in text_sample if ord(char) in telugu_range)
            
            # Check for Kannada script
            kannada_range = range(0x0C80, 0x0CFF)
            kannada_chars = sum(1 for char in text_sample if ord(char) in kannada_range)
            
            # Check for Malayalam script
            malayalam_range = range(0x0D00, 0x0D7F)
            malayalam_chars = sum(1 for char in text_sample if ord(char) in malayalam_range)
            
            # Determine most likely language
            script_counts = {
                'hi': devanagari_chars,
                'bn': bengali_chars,
                'gu': gujarati_chars,
                'pa': gurmukhi_chars,
                'ta': tamil_chars,
                'te': telugu_chars,
                'kn': kannada_chars,
                'ml': malayalam_chars
            }
            
            # Find the script with maximum characters
            max_script = max(script_counts, key=script_counts.get)
            
            # If no Indian script detected, assume English
            if script_counts[max_script] == 0:
                detected_lang = 'en'
                confidence = 0.8
            else:
                detected_lang = max_script
                confidence = min(0.9, script_counts[max_script] / len(text_sample))
            
            return {
                "success": True,
                "detected_language": self.supported_languages.get(detected_lang, 'Unknown'),
                "language_code": detected_lang,
                "confidence": round(confidence, 2),
                "script_counts": script_counts
            }
            
        except Exception as e:
            return {"error": f"Language detection failed: {str(e)}"}

    def get_supported_languages(self) -> Dict[str, Any]:
        """Get list of supported languages"""
        return {
            "supported_languages": self.supported_languages,
            "total_count": len(self.supported_languages),
            "indic_languages": {k: v for k, v in self.supported_languages.items() if k != 'en'}
        }

    async def translate_to_multiple_languages(self, text: str, src_lang: str, 
                                            target_languages: List[str]) -> Dict[str, Any]:
        """
        Translate text to multiple target languages
        Args:
            text: Text to translate
            src_lang: Source language code
            target_languages: List of target language codes
        Returns:
            Dictionary with translations to all target languages
        """
        try:
            translations = {}
            
            for tgt_lang in target_languages:
                result = await self.translate(text, src_lang, tgt_lang)
                translations[tgt_lang] = result
            
            successful_count = sum(1 for t in translations.values() if t.get("success"))
            
            return {
                "success": successful_count > 0,
                "source_text": text,
                "source_language": self.supported_languages[src_lang],
                "translations": translations,
                "target_languages": target_languages,
                "successful_count": successful_count,
                "total_count": len(target_languages)
            }
            
        except Exception as e:
            return {"error": f"Multi-language translation failed: {str(e)}"}

# Global instance
translation_service = IndicTrans2Service()
