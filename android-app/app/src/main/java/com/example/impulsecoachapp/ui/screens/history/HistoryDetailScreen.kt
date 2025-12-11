package com.example.impulsecoachapp.ui.screens.history

import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DrawerValue
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ModalNavigationDrawer
import androidx.compose.material3.ModalDrawerSheet
import androidx.compose.material3.NavigationDrawerItem
import androidx.compose.material3.Text
import androidx.compose.material3.rememberDrawerState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import kotlinx.coroutines.launch
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.filled.Menu
import androidx.compose.material3.*
import androidx.compose.runtime.remember
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import com.example.impulsecoachapp.ui.screens.chat.MessageList

@Composable
fun HistoryDetailScreen(
    threadId: String,
    onBackPressed: () -> Unit,
    onOpenHistory: (String) -> Unit,
    onNavigateToChat: () -> Unit,
    viewModel: HistoryDetailViewModel = hiltViewModel()
) {
    val messages by viewModel.messages.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    val errorMessage by viewModel.errorMessage.collectAsState()
    val historyList by viewModel.historyList.collectAsState()
    val isWeeklyModeLocked by viewModel.isWeeklyModeLocked.collectAsState() // 잠금 상태 구독
    val context = LocalContext.current // Toast 띄우기 위한 Context
    val currentSessionTitle = remember(historyList, threadId) { // 현재 threadId에 해당하는 제목 찾기
        historyList.find { it.sessionId == threadId }?.title ?: "상담 기록" // historyList가 아직 로드되지 않았거나 못 찾으면 기본값 "상담 기록" 표시
    }

    val drawerState = rememberDrawerState(initialValue = DrawerValue.Closed) // 서랍
    val scope = rememberCoroutineScope()

    LaunchedEffect(Unit) { // 새로운 세션 생성 시 chatscreen으로 이동하도록 뷰모델에서 신호가 오면 실행
        viewModel.navigateToChatEvent.collect {
            onNavigateToChat()
        }
    }
    LaunchedEffect(threadId) {
        viewModel.loadHistory(threadId)
        viewModel.loadHistoryList() // 필요한 경우
    }

    ModalNavigationDrawer(
        drawerState = drawerState, // 상태 연결 필수
        drawerContent = {
            ModalDrawerSheet {
                Text(
                    text = "currentSessionTitle",
                    modifier = Modifier.padding(16.dp),
                    style = MaterialTheme.typography.titleMedium
                )
                HorizontalDivider() // Material3에서는 Divider 대신 HorizontalDivider 권장

                // [NEW CHAT 버튼]
                NavigationDrawerItem(
                    label = {
                        Text(
                            text = if (isWeeklyModeLocked) "✨ 새 FAQ 시작하기 (🔒)" else "✨ 새 FAQ 시작하기",
                            color = if (isWeeklyModeLocked) Color.Gray else MaterialTheme.colorScheme.onSurface
                        )
                    },
                    selected = false,
                    onClick = {
                        if (isWeeklyModeLocked) {
                            Toast.makeText(context, "현재 진행 중인 주간 상담을 먼저 마무리해 주세요!", Toast.LENGTH_SHORT)
                                .show()
                        }
                        else{
                            viewModel.onNewSessionClick()
                            scope.launch { drawerState.close() } // 클릭 후 서랍 닫기
                        }
                    }
                )

                HorizontalDivider()

                // [과거 기록 리스트]
                LazyColumn {
                    items(historyList) { session ->
                        NavigationDrawerItem(
                            label = { Text(session.title) },
                            badge = { Text(session.date) },
                            selected = false,
                            onClick = {
                                onOpenHistory(session.sessionId) //historydetailscreen으로 이동
                                scope.launch { drawerState.close() }
                            }
                        )
                    }
                }
            }
        }
    ) {
        // ChatScreenContent와 비슷한 구조로 맞추기
        Column(
            modifier = Modifier
                .fillMaxSize()
                .background(Color(0xFFF7F6FB))
                .padding(
                    top = WindowInsets.statusBars
                        .asPaddingValues()
                        .calculateTopPadding(),
                    start = 16.dp,
                    end = 16.dp
                )
                .windowInsetsPadding(
                    WindowInsets.ime.union(WindowInsets(bottom = 0.dp))
                )
        ) {
            // ✅ 여기서 TopSessionBar 재사용 + 뒤로가기만 켜기
            TopSessionBar(
                title = "지난 상담 & 새 채팅",
                onMenuClick = { scope.launch { drawerState.open() } },
                onBackPressed = onBackPressed
            )

            Box(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth()
                    .padding(12.dp)
            ) {
                when {
                    isLoading -> {
                        CircularProgressIndicator(
                            modifier = Modifier.align(Alignment.Center)
                        )
                    }

                    errorMessage != null -> {
                        Text(
                            text = errorMessage ?: "기록을 불러오지 못했습니다.",
                            color = MaterialTheme.colorScheme.error,
                            modifier = Modifier
                                .align(Alignment.Center)
                                .padding(16.dp)
                        )
                    }

                    else -> {
                        // ✅ ChatScreen과 동일한 MessageList 재사용
                        MessageList(
                            messages = messages,
                            isLoading = isLoading,
                            loadingStage = null,
                            modifier = Modifier.fillMaxSize()
                        )
                    }
                }
            }
        }
    }
}


// 메뉴 아이콘이 있는 상단 바
@Composable
fun TopSessionBar(
    title: String,
    onMenuClick: () -> Unit,
    onBackPressed: (() -> Unit)? = null
) {
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
            // ✅ 히스토리 화면에서만 쓸 뒤로가기 버튼
            if (onBackPressed != null) {
                IconButton(onClick = onBackPressed) {
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                        contentDescription = "뒤로가기",
                        tint = Color(0xFF6200EE)
                    )
                }
            }

            // 햄버거 메뉴 아이콘
            IconButton(onClick = onMenuClick) {
                Icon(
                    imageVector = Icons.Default.Menu,
                    contentDescription = "메뉴 열기",
                    tint = Color(0xFF6200EE)
                )
            }

            Text(
                text = title,
                style = MaterialTheme.typography.titleMedium,
                color = Color(0xFF6200EE),
                fontWeight = FontWeight.Bold,
                modifier = Modifier.padding(start = 8.dp)
            )
        }
    }
}
