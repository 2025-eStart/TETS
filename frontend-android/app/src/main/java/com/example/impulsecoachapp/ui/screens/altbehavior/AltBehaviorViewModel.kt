package com.example.impulsecoachapp.ui.screens.altbehavior
import androidx.lifecycle.ViewModel
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue

enum class AltStep {
    Intro, Timer, BridgeToChat
}

class AltBehaviorViewModel : ViewModel() {
    var currentStep by mutableStateOf(AltStep.Intro)
        private set

    fun goToTimer() {
        currentStep = AltStep.Timer
    }

    fun goToBridge() {
        currentStep = AltStep.BridgeToChat
    }

    fun reset() {
        currentStep = AltStep.Intro
    }
}
