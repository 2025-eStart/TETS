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
        // route를 "Chat?threadId={threadId}" 형태로 변경하여 선택적 파라미터 수신
        composable(
            route = "${BottomTab.Chat.name}?threadId={threadId}",
            arguments = listOf(
                navArgument("threadId") {
                    type = NavType.StringType
                    nullable = true // 없으면(null) 평소처럼 최신 세션 로드
                    defaultValue = null
                }
            )
        ) { backStackEntry ->
            // URL에서 threadId 꺼내기 (없으면 null)
            val targetThreadId = backStackEntry.arguments?.getString("threadId")

            ChatScreen(
                targetThreadId = targetThreadId,
                selectedTab = BottomTab.Chat,
                onTabSelected = onTabSelected,
                onBackPressed = { }, // 메인 화면에서는 뒤로가기를 눌러도 특별한 동작이 없거나 앱 종료(시스템 처리)
                //  onOpenHistory 파라미터 전달
                onOpenHistory = { threadId ->
                    // 히스토리 상세 화면으로 이동 (인자 전달)
                    navController.navigate("history_detail/$threadId")
                },
                // [NEW] "채팅 이어하기" 콜백 (서랍에서 General 눌렀을 때)
                onOpenChat = { threadId ->
                    // 1. 스택 정리 (기존 채팅/히스토리 화면들 치우기)
                    navController.navigate("${BottomTab.Chat.name}?threadId=$threadId") {
                        popUpTo(navController.graph.startDestinationId) { inclusive = true }
                        launchSingleTop = true
                    }
                }
            )
        }

        //  히스토리 상세 화면 네비게이션 추가
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
                    navController.navigate("history_detail/$newId")
                },
                onOpenChat = { threadId ->
                    navController.navigate("${BottomTab.Chat.name}?threadId=$threadId") {
                        popUpTo(navController.graph.startDestinationId) { inclusive = true }
                        launchSingleTop = true
                    }
                },

                // 과거 채팅 내역 조회 화면에서 새로운 세션 열었을 때 채팅 화면으로 이동하는 로직 연결
                onNavigateToChat = {
                    // 1. 채팅 탭(홈)으로 이동
                    navController.navigate(BottomTab.Chat.name) {
                        // 2. 백스택 정리 (뒤로가기 눌렀을 때 다시 히스토리 화면이 나오지 않도록 'startDestination'(채팅화면)까지의 쌓인 화면들을 모두 clear)
                        popUpTo(navController.graph.startDestinationId) {
                            inclusive = false // 채팅 화면 자체는 남겨둠
                        }
                        // 3. 이미 채팅 화면이 최상단에 있다면 새로 만들지 않음
                        launchSingleTop = true
                    }
                }
            )
        }
    }
}