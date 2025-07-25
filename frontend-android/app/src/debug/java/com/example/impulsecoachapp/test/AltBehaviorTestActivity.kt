package com.example.impulsecoachapp.test

import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.example.impulsecoachapp.ui.screens.altbehavior.AltBehaviorScreenWithLog
import com.example.impulsecoachapp.ui.theme.ImpulseCoachAppTheme

class AltBehaviorTestActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Log.d("AltTest", "🟢 AltBehavior 테스트 액티비티 실행됨")

        setContent {
            ImpulseCoachAppTheme {
                AltBehaviorScreenWithLog()
            }
        }
    }
}