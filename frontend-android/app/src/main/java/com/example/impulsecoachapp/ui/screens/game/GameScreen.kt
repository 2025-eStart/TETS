package com.example.impulsecoachapp.ui.screens.game

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import com.example.impulsecoachapp.ui.components.BottomTab
import com.example.impulsecoachapp.ui.components.ScreenScaffold

@Composable
fun GameScreen(
    selectedTab: BottomTab,
    onTabSelected: (BottomTab) -> Unit
) {
    ScreenScaffold(
        selectedTab = selectedTab,
        onTabSelected = onTabSelected
    ) {
        Column(modifier = Modifier.fillMaxSize()) {
            Text("게임 화면입니다.")
        }
    }
}
