# google_mlkit_text_recognition references optional OCR scripts from its platform channel.
# Cardbook currently uses Latin OCR only, so release builds can ignore missing optional script classes.
-dontwarn com.google.mlkit.vision.text.chinese.**
-dontwarn com.google.mlkit.vision.text.devanagari.**
-dontwarn com.google.mlkit.vision.text.japanese.**
-dontwarn com.google.mlkit.vision.text.korean.**
