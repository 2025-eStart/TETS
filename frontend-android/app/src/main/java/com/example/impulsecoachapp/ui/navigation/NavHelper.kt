package com.example.impulsecoachapp.ui.navigation

import androidx.navigation.NavController
import com.example.impulsecoachapp.viewmodel.UserViewModel

fun NavController.logoutAndNavigateToLogin(
    userViewModel: UserViewModel,
    defaultPopUpToRoute: String = "home"
) {
    val currentRoute = this.currentBackStackEntry?.destination?.route ?: defaultPopUpToRoute
    userViewModel.logout()
    this.navigate("login") {
        popUpTo(currentRoute) { inclusive = true }
    }
}
