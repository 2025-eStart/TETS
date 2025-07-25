// 이 파일은 앱의 모든 화면(Screen)들을 등록하고, 어떤 경로(route)로 각 화면에 접근할지를 정의하는 교통 관제탑
// 사용자가 홈 화면에서 버튼을 누르거나, 다른 화면에서 특정 동작을 했을 때 특정 화면으로 이동시키는 흐름을 만들려면 반드시 이곳에 등록해야 함.

package com.example.impulsecoachapp.ui.screens.altbehavior

import android.util.Log // ✅ Log import 추가
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavController
import com.example.impulsecoachapp.ui.components.BottomTab
import com.example.impulsecoachapp.ui.components.ScreenScaffold
import com.example.impulsecoachapp.viewmodels.UserViewModel

@Composable
fun AltBehaviorScreen(
    selectedTab: BottomTab,
    onTabSelected: (BottomTab) -> Unit,
    viewModel: AltBehaviorViewModel = viewModel(),
    userViewModel: UserViewModel = viewModel(),
    navController: NavController
) {
    // ✅ 화면이 그려지기 직전의 상태를 기록
    Log.d("AltBehaviorDebug", "AltBehaviorScreen이 그려집니다. 현재 상태: ${viewModel.currentStep}")


    // 1. 현재 단계에 따라 보여줄 "내용물"을 미리 정합니다.
    val content: @Composable () -> Unit = {
        when (viewModel.currentStep) {
            AltStep.Intro -> IntroSection(onStart = { viewModel.goToTimer() })
            AltStep.Timer -> TimerSection(onFinish = { viewModel.goToBridge() })
            AltStep.BridgeToChat -> BridgeToChatSection(onDone = { viewModel.reset() })
        }
    }

    // 2. 현재 단계가 Timer일 때와 아닐 때를 구분하여 "틀"을 결정합니다.
    if (viewModel.currentStep == AltStep.Timer) {
        // Timer일 경우: 네비게이션 바가 없는 일반 틀 사용
        content()
    } else {
        // 그 외의 경우: 네비게이션 바가 있는 ScreenScaffold 틀 사용
        ScreenScaffold(
            modifier = Modifier.border(2.dp, Color.Red),
            selectedTab = selectedTab,
            onTabSelected = onTabSelected
        ) { innerPadding ->
            Box(modifier = Modifier.padding(innerPadding)) {
                content()
            }
        }
    }
}