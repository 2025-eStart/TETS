package com.example.impulsecoachapp.ui.screens.altbehavior

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import com.example.impulsecoachapp.ui.sound.AltBehaviorSoundPlayer
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

class TimerViewModel(application: Application) : AndroidViewModel(application) {
    private val soundPlayer = AltBehaviorSoundPlayer(application)

    private val _phase = MutableStateFlow(BreathingPhase.Inhale)
    val phase = _phase.asStateFlow()

    fun setPhase(phase: BreathingPhase) {
        _phase.value = phase
    }

    fun playPhaseSound() {
        soundPlayer.play()
    }

    fun releaseSound() {
        soundPlayer.release()
    }
}
