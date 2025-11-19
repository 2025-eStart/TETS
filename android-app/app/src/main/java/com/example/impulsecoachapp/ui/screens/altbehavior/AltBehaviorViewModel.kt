package com.example.impulsecoachapp.ui.screens.altbehavior

import android.util.Log // ✅ Log import 추가
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

    // ✅ ViewModel이 생성되는 시점을 기록하기 위해 init 블록 추가
    init {
        Log.d("AltBehaviorDebug", "ViewModel이 생성되었습니다. 초기 상태: $currentStep")
    }

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
