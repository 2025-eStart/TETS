package com.example.impulsecoachapp.ui.sound

import android.content.Context
import android.media.SoundPool
import com.example.impulsecoachapp.R

class AltBehaviorSoundPlayer(context: Context) {
    private val soundPool: SoundPool = SoundPool.Builder().setMaxStreams(3).build()
    private val bowlSound = soundPool.load(context, R.raw.sound_singing_bowl, 1)
    private var bowlPlayed = false
    fun play() {
        if (!bowlPlayed) {
            soundPool.play(bowlSound, 1f, 1f, 1, 0, 1f)
            bowlPlayed = true
        }
    }

    fun release() {
        soundPool.release()
    }
}
