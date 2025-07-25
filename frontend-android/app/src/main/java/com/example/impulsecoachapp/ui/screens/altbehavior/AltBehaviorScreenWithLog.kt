package com.example.impulsecoachapp.ui.screens.altbehavior

import android.util.Log
import androidx.compose.animation.Crossfade
import androidx.compose.runtime.Composable
import androidx.lifecycle.viewmodel.compose.viewModel

@Composable
fun AltBehaviorScreenWithLog(
    viewModel: AltBehaviorViewModel = viewModel()
) {
    val step = viewModel.currentStep

    Crossfade(targetState = step, label = "AltStepTransition") { current ->
        when (current) {
            AltStep.Intro -> {
                Log.d("AltTest", "📍 현재 화면: Intro")
                IntroSection(onStart = {
                    Log.d("AltTest", "▶️ Intro → Timer로 전환")
                    viewModel.goToTimer()
                })
            }

            AltStep.Timer -> {
                Log.d("AltTest", "📍 현재 화면: Timer")
                TimerSection(
                    onFinish = {
                        Log.d("AltTest", "⏰ 타이머 종료 → BridgeToChat")
                        viewModel.goToBridge()
                    },
                    onInterrupt = {
                        Log.d("AltTest", "🛑 터치로 중단 → BridgeToChat")
                        viewModel.goToBridge()
                    }
                )
            }

            AltStep.BridgeToChat -> {
                Log.d("AltTest", "📍 현재 화면: BridgeToChat")
                BridgeToChatSection(onDone = {
                    Log.d("AltTest", "🔁 리셋 → Intro")
                    viewModel.reset()
                })
            }
        }
    }
}

