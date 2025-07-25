package com.example.impulsecoachapp.ui.screens.altbehavior

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun BridgeToChatSection(
    onDone: () -> Unit
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .clickable { onDone() }, // 화면 아무데나 누르면 IntroSection으로 돌아감
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(
                text = "지금 기분은 어때요?",
                fontSize = 24.sp
            )
            Spacer(modifier = Modifier.height(24.dp))
            Button(
                onClick = { /* TODO: 실제 상담 화면으로 이동하도록 연결 */ },
                modifier = Modifier.padding(16.dp)
            ) {
                Text("상담 시작하기")
            }
        }
    }
}
