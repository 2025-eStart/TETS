// app.MainActivity
package com.example.impulsecoachapp

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.core.view.WindowCompat
import com.example.impulsecoachapp.ui.ImpulseCoachApp
import com.example.impulsecoachapp.ui.theme.ImpulseCoachAppTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // 앱이 시스템 바(상태, 네비게이션) 뒤에 그려지도록 허용합니다.
        WindowCompat.setDecorFitsSystemWindows(window, false)
        setContent {
            ImpulseCoachAppTheme {
                // A surface container using the 'background' color from the theme
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    ImpulseCoachApp()
                }
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
fun DefaultPreview() {
    ImpulseCoachAppTheme {
        ImpulseCoachApp()
    }
}
