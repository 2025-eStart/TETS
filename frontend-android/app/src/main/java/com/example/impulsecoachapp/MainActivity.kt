package com.example.impulsecoachapp

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import com.example.impulsecoachapp.ui.screens.MainScreen
import com.example.impulsecoachapp.ui.theme.ImpulseCoachAppTheme
import com.example.impulsecoachapp.utils.PermissionUtils
import com.example.impulsecoachapp.viewmodels.MainViewModel

class MainActivity : ComponentActivity() {

    // ✅ by viewModels()를 통해 ViewModel 인스턴스 생성
    private val viewModel: MainViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            ImpulseCoachAppTheme {
                MainScreen(
                    uiState = viewModel.uiState,
                    onDialogDismissed = viewModel::onDialogDismissed
                )
            }
        }
    }

    override fun onResume() {
        super.onResume()
        // ✅ 권한 확인 후, 결과를 ViewModel에 전달
        val isGranted = PermissionUtils.isNotificationPermissionGranted(this)
        viewModel.onPermissionResult(isGranted)
    }
}
