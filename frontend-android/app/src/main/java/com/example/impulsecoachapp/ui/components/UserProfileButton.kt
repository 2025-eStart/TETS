package com.example.impulsecoachapp.ui.components

import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.IconButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import com.example.impulsecoachapp.R

@Composable
fun UserProfileButton(
    onSettingsClick: () -> Unit,
    onLogoutClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    var expanded by remember { mutableStateOf(false) }

    IconButton(onClick = { expanded = true }, modifier = modifier) {
        Image(
            painter = painterResource(id = R.drawable.ic_user_profile),
            contentDescription = "User Profile",
            modifier = Modifier
                .size(36.dp)
                .clip(CircleShape)
        )
    }

    DropdownMenu(
        expanded = expanded,
        onDismissRequest = { expanded = false }
    ) {
        DropdownMenuItem(
            text = { Text("설정") },
            onClick = {
                expanded = false
                onSettingsClick()
            }
        )
        DropdownMenuItem(
            text = { Text("로그아웃") },
            onClick = {
                expanded = false
                onLogoutClick()
            }
        )
    }
}
