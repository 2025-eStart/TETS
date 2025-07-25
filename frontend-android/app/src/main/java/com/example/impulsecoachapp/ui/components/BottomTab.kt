package com.example.impulsecoachapp.ui.components

import com.example.impulsecoachapp.R

// BottomTab.kt (새 파일 또는 NavBarLight.kt 상단에 임시로 정의)
enum class BottomTab(val label: String, val iconRes: Int) {
    Game("게임", R.drawable.ic_game),
    Chat("상담", R.drawable.ic_chat),
    AltBehavior("심호흡", R.drawable.ic_breathe),
    Report("레포트", R.drawable.ic_report)
}