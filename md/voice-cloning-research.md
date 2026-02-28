# Voice Cloning & Song Translation Research

## Single-Track Voice Cloning (Speech)
- **ElevenLabs**: 30s clip, instant clone, best quality. $5/mo+. Speech only — no singing.
- **Fish Speech**: 5-10s, Apache 2.0, fast, multilingual. Open source.
- **F5-TTS**: 3s clip, best quality from short clips. CC-BY-NC (non-commercial).
- **CosyVoice 3** (Alibaba): 3-10s, Apache 2.0, 9 languages + 18 Chinese dialects.
- **GPT-SoVITS v4**: 5s zero-shot / 1min fine-tune. MIT. Speech + some singing.
- **XTTS v2** (Coqui): 6s, 17 languages. CPML license (Coqui defunct). Unmaintained.
- **OpenVoice V2**: MIT, cross-lingual, good tone color transfer but speech-only.

## Song Translation Pipeline (How AI Covers Are Made)

### Standard proven pipeline (RVC-based)
```
Original Song
  → UVR5 / Demucs (separate vocals from instrumental)
  → ChatGPT / Claude (translate lyrics — syllable-matched to melody)
  → Human sings translated lyrics as "guide vocal"
  → RVC v2 with pre-trained artist model (converts voice timbre)
  → DAW (mix converted vocal + original instrumental)
```

### Key tools per step
1. **Vocal separation**: Demucs (htdemucs_ft), UVR5, LALAL.ai
2. **Transcription**: Whisper large-v3 (~85-90% on singing)
3. **Lyrics translation**: Claude/GPT-4 with syllable constraints + manual revision
4. **Guide vocal**: Human singing (most common), ACE Studio SVS, or TTS (poor for singing)
5. **Voice conversion**: RVC v2 (dominant), So-VITS-SVC (declining), Seed-VC (emerging)
6. **Mixing**: FFmpeg, Audacity, any DAW

### RVC specifics
- 5-10 min of clean vocal audio to train
- 30-60 min training on GPU (300-600 epochs)
- Use RMVPE pitch extraction
- Do NOT enable "automatic pitch prediction" for singing
- Pre-trained models for many artists available on voice-models.com, Weights.com, AI Hub Discord

### ElevenLabs limitations for singing
- No voice_id param in Eleven Music API (can't use cloned voice)
- Dubbing Studio = speech only, passes music through
- Voice Changer (speech-to-speech) flattens melody when fed singing
- **Conclusion: ElevenLabs cannot do singing voice cloning. Use for speech/audiobooks only.**

## Automation tools
- **AICoverGen**: github.com/SociallyIneptWeeb/AICoverGen — full pipeline from YouTube URL
- **Ultimate RVC**: github.com/JackismyShephard/ultimate-rvc — WebUI for each step
- **ardha27/AI-Song-Cover-RVC**: All-in-one Google Colab

## Communities
- AI Hub Discord: 537k+ members, 20k+ voice models
- Weights.com (shutting down March 2026)
- voice-models.com: 27.9k+ models
