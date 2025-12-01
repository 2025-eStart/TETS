package com.example.impulsecoachapp.ui.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import com.example.impulsecoachapp.ui.components.BottomTab
import com.example.impulsecoachapp.ui.screens.chat.ChatScreen
import com.example.impulsecoachapp.ui.screens.history.HistoryDetailScreen

@Composable
fun AppNavHost(
    navController: NavHostController,
    currentTab: BottomTab,
    onTabSelected: (BottomTab) -> Unit
) {
    NavHost(
        navController = navController,
        startDestination = BottomTab.Chat.name
    ) {

        // 1. 메인 채팅 화면
        composable(BottomTab.Chat.name) {
            ChatScreen(
                selectedTab = BottomTab.Chat,
                onTabSelected = onTabSelected,
                // 메인 화면에서는 뒤로가기를 눌러도 특별한 동작이 없거나 앱 종료(시스템 처리)
                onBackPressed = { },

                // ✅ [수정 1] 누락되었던 onOpenHistory 파라미터 전달
                onOpenHistory = { threadId ->
                    // 히스토리 상세 화면으로 이동 (인자 전달)
                    navController.navigate("history_detail/$threadId")
                }
            )
        }

        // ✅ [수정 2] 히스토리 상세 화면 네비게이션 추가
        // "history_detail/{threadId}" 형식으로 주소를 정의하여 ID를 받습니다.
        composable(
            route = "history_detail/{threadId}",
            arguments = listOf(navArgument("threadId") { type = NavType.StringType })
        ) { backStackEntry ->
            // URL에서 threadId 추출
            val threadId = backStackEntry.arguments?.getString("threadId") ?: return@composable

            HistoryDetailScreen(
                threadId = threadId,
                onBackPressed = { navController.popBackStack() }, // 뒤로가기 시 스택에서 제거
                onOpenHistory = { newId ->
                    // 히스토리 화면에서 또 다른 히스토리를 누른 경우
                    navController.navigate("history_detail/$newId") {
                        // (선택사항) 기존 히스토리를 스택에서 지우고 싶다면 설정 추가 가능
                        popUpTo(BottomTab.Chat.name) { saveState = true }
                    }
                }
            )
        }
    }
}