// 결제 내역 푸시 알림 받아오기 하면서 MainActivity.kt를 viewmodel, screen으로 분리
package com.example.impulsecoachapp.ui.screens

import android.content.Intent
import android.provider.Settings
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import com.example.impulsecoachapp.ui.ImpulseCoachApp
import com.example.impulsecoachapp.viewmodels.MainUiState

@Composable
fun MainScreen(uiState: MainUiState, onDialogDismissed: () -> Unit) {
    val context = LocalContext.current

    Box(modifier = Modifier.fillMaxSize()) {
        Surface(
            modifier = Modifier.fillMaxSize(),
            color = MaterialTheme.colorScheme.background
        ) {
            ImpulseCoachApp()
        }

        if (uiState.showPermissionDialog) {
            PermissionDialog(
                onConfirm = {
                    context.startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))
                    onDialogDismissed()
                },
                onDismiss = onDialogDismissed
            )
        }
    }
}

// MainScreen.kt 파일 하단에 두어 관련된 UI 요소임을 명시
@Composable
private fun PermissionDialog(onConfirm: () -> Unit, onDismiss: () -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(text = "알림 접근 권한 필요") },
        text = { Text(text = "소비 내역 자동 기록을 위해 결제 알림을 읽을 수 있는 권한이 필요합니다.") },
        confirmButton = { TextButton(onClick = onConfirm) { Text("설정으로 이동") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("취소") } }
    )
}