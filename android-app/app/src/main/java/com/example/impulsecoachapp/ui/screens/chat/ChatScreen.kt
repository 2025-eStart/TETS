//ui.screens.ChatScreen.kt
package com.example.impulsecoachapp.ui.screens.chat

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material.icons.filled.Menu
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.example.impulsecoachapp.R
import com.example.impulsecoachapp.domain.model.ChatMessage
import com.example.impulsecoachapp.ui.components.BottomTab
import com.example.impulsecoachapp.ui.components.ScreenScaffold
import kotlinx.coroutines.launch

@Composable
fun ChatScreen(
    selectedTab: BottomTab,
    onTabSelected: (BottomTab) -> Unit,
    onBackPressed: () -> Unit,
    onOpenHistory: (String) -> Unit,          // ✅ 추가: 과거 채팅 threadId 넘겨줄 콜백
    viewModel: ChatViewModel = hiltViewModel()
) {
    val messages by viewModel.messages.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    val isSessionEnded by viewModel.isSessionEnded.collectAsState()
    val sessionTitle by viewModel.sessionTitle.collectAsState()
    val sessionGoals by viewModel.sessionGoals.collectAsState()
    val historyList by viewModel.historyList.collectAsState()

    // 서랍 상태 관리 변수 추가
    val drawerState = rememberDrawerState(initialValue = DrawerValue.Closed)
    val scope = rememberCoroutineScope()

    ModalNavigationDrawer(
        drawerState = drawerState, // 상태 연결 필수
        drawerContent = {
            ModalDrawerSheet {
                Text(
                    text = "지난 대화 & 새 채팅",
                    modifier = Modifier.padding(16.dp),
                    style = MaterialTheme.typography.titleMedium
                )
                HorizontalDivider() // Material3에서는 Divider 대신 HorizontalDivider 권장

                // [NEW CHAT 버튼]
                NavigationDrawerItem(
                    label = { Text("✨ 새로운 상담 시작하기") },
                    selected = false,
                    onClick = {
                        viewModel.onNewSessionClick()
                        scope.launch { drawerState.close() } // 클릭 후 서랍 닫기
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
        ScreenScaffold(
            selectedTab = selectedTab,
            onTabSelected = onTabSelected
        ) { innerPadding ->
            ChatScreenContent(
                modifier = Modifier,
                innerPadding = innerPadding,
                messages = messages,
                isLoading = isLoading,
                isSessionEnded = isSessionEnded,
                sessionTitle = sessionTitle,
                sessionGoals = sessionGoals,
                onSendMessage = { viewModel.sendMessage(it) },
                // [수정 3] 메뉴 버튼 클릭 이벤트 전달
                onMenuClick = { scope.launch { drawerState.open() } }
            )
        }
    }
}

@Composable
fun ChatScreenContent(
    modifier: Modifier = Modifier,
    innerPadding: PaddingValues,
    messages: List<ChatMessage>,
    isLoading: Boolean,
    isSessionEnded: Boolean,
    sessionTitle: String,
    sessionGoals: List<String>,
    onSendMessage: (String) -> Unit,
    onMenuClick: () -> Unit // 메뉴 클릭 콜백 추가
) {
    val layoutDirection = LocalLayoutDirection.current
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(Color(0xFFF7F6FB))
            .padding(
                top = innerPadding.calculateTopPadding(),
                start = innerPadding.calculateStartPadding(layoutDirection),
                end = innerPadding.calculateEndPadding(layoutDirection)
            )
            .windowInsetsPadding(
                WindowInsets.ime.union(WindowInsets(bottom = innerPadding.calculateBottomPadding()))
            )
    ) {
        // [수정 4] 상단 바에 메뉴 클릭 이벤트 전달
        TopSessionBar(title = sessionTitle, onMenuClick = onMenuClick)

        MessageList(
            messages = messages,
            modifier = Modifier.weight(1f)
        )
        UserInput(
            isLoading = isLoading,
            isSessionEnded = isSessionEnded,
            onSendMessage = onSendMessage
        )
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

@Composable
fun UserInput(
    isLoading: Boolean,
    isSessionEnded: Boolean,
    onSendMessage: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    var text by remember { mutableStateOf("") }

    if (isSessionEnded) {
        Text(
            text = "상담이 종료되었습니다.",
            modifier = modifier
                .fillMaxWidth()
                .padding(16.dp),
            color = Color.Gray,
            textAlign = TextAlign.Center
        )
        return
    }

    Row(
        modifier = modifier
            .fillMaxWidth()
            .background(Color.White)
            .padding(8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        OutlinedTextField(
            value = text,
            onValueChange = { text = it },
            modifier = Modifier.weight(1f),
            placeholder = { Text("메시지를 입력하세요...", color = Color.Gray) },
            enabled = !isLoading,
            colors = TextFieldDefaults.colors(
                focusedContainerColor = Color(0xFFF7F6FB),
                unfocusedContainerColor = Color(0xFFF7F6FB),
                disabledContainerColor = Color(0xFFF0F0F0),
                focusedIndicatorColor = Color.Transparent,
                unfocusedIndicatorColor = Color.Transparent,
                focusedTextColor = Color.Black,
                unfocusedTextColor = Color.Black
            ),
            shape = RoundedCornerShape(12.dp)
        )
        Spacer(modifier = Modifier.width(8.dp))

        if (isLoading) {
            CircularProgressIndicator(modifier = Modifier.size(48.dp))
        } else {
            IconButton(
                onClick = {
                    if (text.isNotBlank()) {
                        onSendMessage(text)
                        text = ""
                    }
                },
                enabled = text.isNotBlank()
            ) {
                Icon(
                    imageVector = Icons.AutoMirrored.Filled.Send,
                    contentDescription = "Send Message",
                    tint = if (text.isNotBlank()) Color(0xFF6200EE) else Color.Gray
                )
            }
        }
    }
}

@Composable
fun MessageList(
    messages: List<ChatMessage>,
    modifier: Modifier = Modifier
) {
    val listState = rememberLazyListState()
    val coroutineScope = rememberCoroutineScope()

    LaunchedEffect(messages.size) {
        if (messages.isNotEmpty()) {
            coroutineScope.launch {
                listState.animateScrollToItem(messages.size - 1)
            }
        }
    }

    LazyColumn(
        state = listState,
        modifier = modifier
            .fillMaxWidth()
            .padding(12.dp)
    ) {
        items(messages) { msg ->
            ChatBubble(message = msg)
            Spacer(modifier = Modifier.height(8.dp))
        }
    }
}

@Composable
fun ChatBubble(message: ChatMessage) {
    when (message) {
        is ChatMessage.GuideMessage -> Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.Start
        ) {
            Image(
                painter = painterResource(id = R.drawable.ic_chatbot),
                contentDescription = "Guide",
                modifier = Modifier.size(28.dp)
            )
            Spacer(modifier = Modifier.width(6.dp))
            Box(
                modifier = Modifier
                    .background(Color(0xFFF0F0F0), shape = RoundedCornerShape(12.dp))
                    .padding(12.dp)
                    .weight(1f, fill = false)
            ) {
                Text(text = message.text, fontSize = 16.sp, color = Color.Black)
            }
        }
        is ChatMessage.UserResponse -> Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.End
        ) {
            Box(
                modifier = Modifier
                    .background(Color(0xFFE9E0FA), shape = RoundedCornerShape(12.dp))
                    .padding(12.dp)
                    .weight(1f, fill = false)
            ) {
                Text(text = message.text, fontSize = 16.sp, color = Color.Black)
            }
        }
    }
}