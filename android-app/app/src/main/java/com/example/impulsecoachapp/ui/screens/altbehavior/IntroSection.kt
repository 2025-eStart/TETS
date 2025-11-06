package com.example.impulsecoachapp.ui.screens.altbehavior

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.impulsecoachapp.ui.resources.ImageResources

@Composable
fun IntroSection(onStart: () -> Unit) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFFF9F9FF)) // 연한 배경
    ) {
        // 1. 사용자 아이콘
        Image(
            painter = painterResource(id = ImageResources.UserProfileIcon), // 너의 리소스 이름에 맞게 수정
            contentDescription = "어린왕자",
            modifier = Modifier
                .padding(16.dp)
                .align(Alignment.TopEnd)
                .size(36.dp)
        )

        // 2. 시작 원 버튼
        Box(
            modifier = Modifier
                .size(200.dp)
                .align(Alignment.Center)
                .clip(CircleShape)
                .background(Color(0xFF0B1D3A)) // 진한 남색
                .clickable(onClick = onStart),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = "시작",
                color = Color.White,
                fontSize = 28.sp,
                fontWeight = FontWeight.Bold
            )
        }

        // 3. 여우 이미지
        Image(
            painter = painterResource(id = ImageResources.ChatbotIcon), // 실제 여우 이미지로 바꿔줘
            contentDescription = "여우",
            modifier = Modifier
                .size(80.dp)
                .align(Alignment.BottomEnd)
                .padding(end = 16.dp, bottom = 48.dp)
        )

        // 4. 말풍선 텍스트
        Surface(
            shape = RoundedCornerShape(16.dp),
            color = Color.White,
            shadowElevation = 4.dp,
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .padding(bottom = 32.dp)
        ) {
            Text(
                text = "함께 심호흡해 보자.\n원의 지도에 따라 너의 호흡에 집중해 봐!",
                modifier = Modifier.padding(16.dp),
                fontSize = 14.sp,
                textAlign = TextAlign.Center
            )
        }
    }
}

@Preview(showBackground = true)
@Composable
fun PreviewIntroSection() {
    IntroSection(onStart = {})
}