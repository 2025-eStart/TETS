package com.example.impulsecoachapp.ui.screens.altbehavior

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavController
import com.example.impulsecoachapp.ui.components.BottomTab
import com.example.impulsecoachapp.ui.components.ScreenScaffold
import com.example.impulsecoachapp.viewmodel.UserViewModel

@Composable
fun AltBehaviorScreen(
    selectedTab: BottomTab,
    onTabSelected: (BottomTab) -> Unit,
    viewModel: AltBehaviorViewModel = viewModel(),
    userViewModel: UserViewModel = viewModel(),
    navController: NavController
) {
    ScreenScaffold(
        selectedTab = selectedTab,
        onTabSelected = onTabSelected
    ) { innerPadding ->

        Box(modifier = Modifier.padding(innerPadding)) {
            when (viewModel.currentStep) {
                AltStep.Intro -> IntroSection(onStart = { viewModel.goToTimer() })
                AltStep.Timer -> TimerSection(onFinish = { viewModel.goToBridge() })
                AltStep.BridgeToChat -> BridgeToChatSection(onDone = { viewModel.reset() })
            }
        }
    }
}
