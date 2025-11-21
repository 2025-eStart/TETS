//ui.components.ScreenScaffold
package com.example.impulsecoachapp.ui.components

import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.exclude
import androidx.compose.foundation.layout.ime
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ScreenScaffold(
    selectedTab: BottomTab,
    onTabSelected: (BottomTab) -> Unit,
    modifier: Modifier = Modifier,
    content: @Composable (PaddingValues) -> Unit
) {
    Scaffold(
        modifier = modifier,
        // [수정 2] Scaffold가 키보드를 무시하도록 설정
        // 이렇게 하면 bottomBar (NavBarLight)가 키보드를 따라 올라오지 않습니다.
        contentWindowInsets = WindowInsets.safeDrawing.exclude(WindowInsets.ime),
        bottomBar = {
            NavBarLight(
                selectedTab = selectedTab,
                onTabSelected = onTabSelected
            )
        },
        content = content
    )
}
