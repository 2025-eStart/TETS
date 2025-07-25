package com.example.impulsecoachapp.ui.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.example.impulsecoachapp.data.model.chat.ChatMessage
import com.example.impulsecoachapp.ui.components.BottomTab
import com.example.impulsecoachapp.ui.screens.altbehavior.AltBehaviorScreen
import com.example.impulsecoachapp.ui.screens.chat.ChatScreen
import com.example.impulsecoachapp.ui.screens.game.GameScreen
import com.example.impulsecoachapp.ui.screens.report.ReportScreen

@Composable
fun AppNavHost(
    navController: NavHostController,
    currentTab: BottomTab,
    onTabSelected: (BottomTab) -> Unit
) {
    // 예시용 더미 메시지
    val sampleMessages = listOf(
        ChatMessage.GuideMessage("안녕! 오늘의 소비 습관을 함께 알아보자!"),
        ChatMessage.UserResponse("네, 좋아요."),
        ChatMessage.ChoiceMessage(listOf("좋았어요", "그저 그랬어요", "별로였어요"))
    )
    NavHost(
        navController = navController,
        startDestination = BottomTab.Report.name
    ) {
        composable(BottomTab.Game.name) {
            GameScreen(
                selectedTab = BottomTab.Game,
                onTabSelected = onTabSelected
            )
        }
        composable(BottomTab.Chat.name) {
            ChatScreen(
                selectedTab = BottomTab.Chat,
                onTabSelected = onTabSelected,
                onBackPressed = { /* TODO: 처리 로직 */ }
            )
        }
        composable(BottomTab.AltBehavior.name) {
            AltBehaviorScreen(
                selectedTab = BottomTab.AltBehavior,
                onTabSelected = onTabSelected,
                navController = navController
            )
        }
        composable(BottomTab.Report.name) {
            ReportScreen(
                selectedTab = BottomTab.Report,
                onTabSelected = onTabSelected
            )
        }
    }
}
