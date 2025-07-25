package com.example.impulsecoachapp.ui

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.navigation.compose.rememberNavController
import com.example.impulsecoachapp.ui.components.BottomTab
import com.example.impulsecoachapp.ui.navigation.AppNavHost

@Composable
fun ImpulseCoachApp() {
    // 1. 네비게이션을 관리하는 NavController 생성
    val navController = rememberNavController()

    // 2. 현재 선택된 탭의 상태를 기억
    var currentTab by remember { mutableStateOf(BottomTab.Report) }

    // 3. AppNavHost를 호출하여 전체 네비게이션 시스템을 구성
    AppNavHost(
        navController = navController,
        currentTab = currentTab,
        onTabSelected = { selectedTab ->
            currentTab = selectedTab
            // 네비게이션 로직: 같은 탭을 다시 눌렀을 때 중복 실행 방지 등
            navController.navigate(selectedTab.name) {
                // 백스택의 맨 위에 하나만 쌓이도록 함
                launchSingleTop = true
                // 이전에 방문한 화면의 상태를 복원
                restoreState = true

                // 시작 목적지에서 '뒤로가기'를 눌렀을 때 앱이 종료되도록 함
                popUpTo(navController.graph.startDestinationId) {
                    saveState = true
                }
            }
        }
    )
}