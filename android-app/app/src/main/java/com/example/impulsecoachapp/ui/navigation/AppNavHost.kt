//ui.navigation.AppNavHost
package com.example.impulsecoachapp.ui.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.example.impulsecoachapp.ui.components.BottomTab
import com.example.impulsecoachapp.ui.screens.chat.ChatScreen

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

        composable(BottomTab.Chat.name) {
            ChatScreen(
                selectedTab = BottomTab.Chat,
                onTabSelected = onTabSelected,
                onBackPressed = { /* TODO: 처리 로직 */ }
            )
        }

    }
}
