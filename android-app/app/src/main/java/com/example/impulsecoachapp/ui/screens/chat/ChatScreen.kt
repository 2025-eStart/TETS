// ui.screens.chat.ChatScreen
package com.example.impulsecoachapp.ui.screens.chat

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.example.impulsecoachapp.R
import com.example.impulsecoachapp.domain.model.ChatMessage
import com.example.impulsecoachapp.ui.components.BottomTab
import com.example.impulsecoachapp.ui.components.ScreenScaffold
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlinx.coroutines.launch

@Composable
fun ChatScreen(
    selectedTab: BottomTab,
    onTabSelected: (BottomTab) -> Unit,
    onBackPressed: () -> Unit,
    viewModel: ChatViewModel = hiltViewModel()
) {
    val messages by viewModel.messages.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    val isSessionEnded by viewModel.isSessionEnded.collectAsState()

    val sessionTitle by viewModel.sessionTitle.collectAsState()
    val sessionGoals by viewModel.sessionGoals.collectAsState()

    // 📌 화면이 처음 구성될 때 한 번만 서버에 "빈 신호" 보내서
    // LangGraph가 첫 턴(닉네임 안내/인사)을 생성하도록 유도
    LaunchedEffect(Unit) {
        viewModel.startSessionIfNeeded()
    }

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
            onSendMessage = { viewModel.sendMessage(it) }
        )
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
    onSendMessage: (String) -> Unit
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
        // 상단 바: 서버에서 내려온 주차/제목 표시
        TopSessionBar(title = sessionTitle)

        // 나중에 목표 리스트 UI 추가하고 싶으면 여기서 sessionGoals 사용
        // if (sessionGoals.isNotEmpty()) { GoalsList(sessionGoals) }

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

// 이하 TopSessionBar / UserInput / TopDateTimeBar / MessageList / ChatBubble 는 그대로 사용
// (이미 잘 구성되어 있어서, 위 로직과 충돌 없음)


/**
 * 3. "Dumb" Composable (Content)
 * - ViewModel을 모르며, 오직 받은 데이터로 UI만 그립니다.
 * - 이 함수는 Preview가 매우 쉽습니다.
 */

/*
@Composable
fun ChatScreenContent(
    modifier: Modifier = Modifier,
    innerPadding: PaddingValues,
    messages: List<ChatMessage>,
    isLoading: Boolean,
    isSessionEnded: Boolean,
    onSendMessage: (String) -> Unit
) {
    // [수정 5] 수평 패딩 계산을 위해 layoutDirection 가져오기
    val layoutDirection = LocalLayoutDirection.current
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(Color(0xFFF7F6FB))
            // [수정 6] 상단과 수평 패딩은 innerPadding에서 직접 가져와 적용합니다.
            .padding(
                top = innerPadding.calculateTopPadding(),
                start = innerPadding.calculateStartPadding(layoutDirection),
                end = innerPadding.calculateEndPadding(layoutDirection)
            )
            // [수정 7] 하단 패딩을 동적으로 계산합니다.
            // 1. 키보드 인셋(ime)과
            // 2. Scaffold의 하단 탭 바 인셋(innerPadding.bottom)을
            // .union()을 사용해 둘 중 '더 큰(max)' 값으로 적용합니다.
            .windowInsetsPadding(
                WindowInsets.ime.union(
                    // innerPadding의 하단 값만 WindowInsets으로 변환하여 union
                    WindowInsets(bottom = innerPadding.calculateBottomPadding())
                )
            )
    ) {
        TopDateTimeBar() // 현재 시간을 표시
        MessageList(
            messages = messages,
            modifier = Modifier.weight(1f)
        )
        UserInput(
            isLoading = isLoading,
            isSessionEnded = isSessionEnded,
            onSendMessage = onSendMessage,
            modifier = Modifier
        )
    }
}
*/

// 새로 만든 상단 바 컴포넌트
@Composable
fun TopSessionBar(title: String) {
    Surface(
        color = Color.White,
        shadowElevation = 4.dp,
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Text(
                text = title,
                style = MaterialTheme.typography.titleMedium,
                color = Color(0xFF6200EE),
                fontWeight = androidx.compose.ui.text.font.FontWeight.Bold
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
            // 플레이스홀더 색상 Gray로 고정
            placeholder = { Text("메시지를 입력하세요...", color = Color.Gray) },
            enabled = !isLoading,
            colors = TextFieldDefaults.colors(
                focusedContainerColor = Color(0xFFF7F6FB),
                unfocusedContainerColor = Color(0xFFF7F6FB),
                disabledContainerColor = Color(0xFFF0F0F0),
                focusedIndicatorColor = Color.Transparent,
                unfocusedIndicatorColor = Color.Transparent,

                // 입력 텍스트 색상 Black으로 고정
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
fun TopDateTimeBar() {
// remember를 사용해 현재 날짜/시간을 계산 (성능 최적화)
    val (currentDate, currentTime) = remember {
        val now = Date()
        val dateFormat = SimpleDateFormat("yyyy.MM.dd.E", Locale.KOREAN)
        val timeFormat = SimpleDateFormat("HH:mm", Locale.KOREAN)
        dateFormat.format(now) to timeFormat.format(now)
    }

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(12.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
// 고정된 텍스트 대신 계산된 변수 사용
        Text(currentDate, fontSize = 14.sp, color = Color.Gray)
        Text(currentTime, fontSize = 14.sp, color = Color.Gray)
        Image(
            painter = painterResource(id = R.drawable.ic_user_profile),
            contentDescription = "User",
            modifier = Modifier.size(32.dp)
        )
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
                // 텍스트 색상 Black으로 고정
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
                // 텍스트 색상 Black으로 고정
                Text(text = message.text, fontSize = 16.sp, color = Color.Black)
            }
        }
    }
}
