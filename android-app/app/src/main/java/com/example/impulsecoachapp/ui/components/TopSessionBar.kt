//ui.components.TopSessionBar
package com.example.impulsecoachapp.ui.components

import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.width
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Menu
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp

// 공통 컴포넌트로 분리된 상단 바
@Composable
fun TopSessionBar(
    title: String,
    onMenuClick: () -> Unit,
    onBackPressed: (() -> Unit)? = null,
    onResetClick: (() -> Unit)? = null,
) {
    val screenWidthDp = LocalConfiguration.current.screenWidthDp
    val titleStyle = if (screenWidthDp < 360) {
        MaterialTheme.typography.titleSmall
    } else {
        MaterialTheme.typography.titleMedium
    }
    val showResetLabel = screenWidthDp >= 380  // 화면 좁으면 아이콘만

    Surface(
        color = Color.White,
        shadowElevation = 4.dp,
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // 뒤로가기 버튼 (HistoryDetailScreen 등에서 사용)
            if (onBackPressed != null) {
                IconButton(onClick = onBackPressed) {
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                        contentDescription = "뒤로가기",
                        tint = Color.Black
                    )
                }
            }

            // 햄버거 메뉴 아이콘
            IconButton(onClick = onMenuClick) {
                Icon(
                    imageVector = Icons.Default.Menu,
                    contentDescription = "메뉴 열기",
                    tint = Color.Black
                )
            }

            // 제목
            Text(
                text = title,
                style = titleStyle,
                color = Color.Black,
                fontWeight = FontWeight.Bold,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                modifier = Modifier
                    .padding(start = 8.dp)
                    .weight(1f)
            )

            // 오른쪽 끝: 초기화 버튼
            if (onResetClick != null) {
                TextButton(
                    onClick = onResetClick,
                    modifier = Modifier.heightIn(min = 32.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.Refresh,
                        contentDescription = "초기화",
                        tint = Color(0xFFD32F2F)
                    )
                    if (showResetLabel) {
                        Spacer(Modifier.width(4.dp))
                        Text(
                            text = "초기화",
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                            color = Color(0xFFC71515),
                            style = MaterialTheme.typography.labelLarge
                        )
                    }
                }
            }


        }
    }
}

