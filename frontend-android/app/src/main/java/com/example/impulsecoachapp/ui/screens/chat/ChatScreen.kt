package com.example.impulsecoachapp.ui.screens.chat

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.impulsecoachapp.R
import com.example.impulsecoachapp.model.chat.ChatMessage
import com.example.impulsecoachapp.ui.components.BottomTab
import com.example.impulsecoachapp.ui.components.ScreenScaffold

@Composable
fun ChatScreen(
    selectedTab: BottomTab,
    onTabSelected: (BottomTab) -> Unit,
    onBackPressed: () -> Unit,
    viewModel: ChatViewModel = viewModel()
) {
    val messages by viewModel.messages.collectAsState()

    ScreenScaffold(
        selectedTab = selectedTab,
        onTabSelected = onTabSelected
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .padding(innerPadding)
                .fillMaxSize()
                .background(Color(0xFFF7F6FB))
        ) {
            TopDateTimeBar()
            MessageList(
                messages = messages,
                onOptionSelected = { viewModel.handleUserSelection(it) },
                modifier = Modifier.weight(1f)
            )
        }
    }
}


@Composable
fun TopDateTimeBar() {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(12.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text("2025.07.01.화요일", fontSize = 14.sp, color = Color.Gray)
        Text("14:03", fontSize = 14.sp, color = Color.Gray)
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
    onOptionSelected: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    LazyColumn(
        modifier = modifier
            .fillMaxWidth()
            .padding(12.dp),
        reverseLayout = true
    ) {
        items(messages.reversed()) { msg ->
            ChatBubble(message = msg, onOptionSelected = onOptionSelected)
            Spacer(modifier = Modifier.height(8.dp))
        }
    }
}

@Composable
fun ChatBubble(message: ChatMessage, onOptionSelected: (String) -> Unit) {
    when (message) {
        is ChatMessage.GuideMessage -> Row {
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
            ) {
                Text(text = message.text, fontSize = 16.sp)
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
            ) {
                Text(text = message.text, fontSize = 16.sp)
            }
        }
        is ChatMessage.ChoiceMessage -> {
            Column {
                message.options.forEach { option ->
                    Button(
                        onClick = { onOptionSelected(option) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 4.dp)
                    ) {
                        Text(option)
                    }
                }
            }
        }
    }
}

@Preview(showSystemUi = true, showBackground = true)
@Composable
fun PreviewChatScreen() {
    ChatScreen(
        selectedTab = BottomTab.Chat,
        onTabSelected = {},
        onBackPressed = {}
    )
}