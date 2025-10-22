package com.example.impulsecoachapp.data

import java.time.LocalTime

data class Transaction(
    val id: String,
    val time: LocalTime,
    val description: String,
    val amount: Int,
    val paymentMethod: String,
    var isImpulseBuy: Boolean = false,
    // 상담 요약 정보 (API를 통해 받아올 데이터)
    val summary: String? = "소비 내용: 배달음식\n원인: 스트레스\n실천할 대체 행동: 10분 산책하기"
)