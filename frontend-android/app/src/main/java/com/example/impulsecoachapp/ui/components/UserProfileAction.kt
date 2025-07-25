package com.example.impulsecoachapp.ui.components

import androidx.compose.runtime.Composable
import androidx.navigation.NavController
import com.example.impulsecoachapp.ui.navigation.logoutAndNavigateToLogin
import com.example.impulsecoachapp.viewmodels.UserViewModel

@Composable
fun UserProfileAction(
    navController: NavController,
    userViewModel: UserViewModel
) {
    UserProfileButton(
        onSettingsClick = { navController.navigate("settings") },
        onLogoutClick = {
            navController.logoutAndNavigateToLogin(userViewModel)
        }
    )
}
