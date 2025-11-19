package com.example.impulsecoachapp.ui.screens.report

// BottomTab과 ScreenScaffold를 import 합니다.
import com.example.impulsecoachapp.ui.components.BottomTab
import com.example.impulsecoachapp.ui.components.ScreenScaffold

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ReportScreen(
    // 1. AppNavHost로부터 받을 파라미터를 추가합니다.
    selectedTab: BottomTab,
    onTabSelected: (BottomTab) -> Unit,
    viewModel: ReportViewModel = viewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    val sheetState = rememberModalBottomSheetState()

    // 2. 기존 Scaffold를 ScreenScaffold로 교체합니다.
    ScreenScaffold(
        selectedTab = selectedTab,
        onTabSelected = onTabSelected
    ) { innerPadding ->
        // 3. ScreenScaffold가 제공하는 innerPadding을 적용합니다.
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding) // 여기에 padding 적용
                .background(Color(0xFF1C1B1F))
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // ReportScreen의 기존 UI 내용들은 그대로 유지됩니다.
            ReportHeader(
                date = uiState.selectedDate,
                onCalendarClick = { viewModel.toggleCalendar(true) }
            )
            Spacer(modifier = Modifier.height(24.dp))
            DailySummaryCard()
            Spacer(modifier = Modifier.height(24.dp))
            TransactionList(
                transactions = uiState.transactions,
                onTransactionClick = { transaction ->
                    viewModel.showTransactionDetails(transaction)
                },
                onImpulseCheckChanged = { transaction, isChecked ->
                    viewModel.onImpulseCheckChanged(transaction, isChecked)
                }
            )
        }
    }

    // ModalBottomSheet와 CalendarDialog는 Scaffold 외부에 위치하므로
    // 그대로 두면 됩니다.
    if (uiState.selectedTransaction != null) {
        ModalBottomSheet(
            onDismissRequest = { viewModel.dismissTransactionDetails() },
            sheetState = sheetState,
            containerColor = Color(0xFF36343B)
        ) {
            TransactionDetailSheet(transaction = uiState.selectedTransaction)
        }
    }

    if (uiState.showCalendar) {
        ReportCalendarDialog(
            initialDate = uiState.selectedDate,
            onDateSelected = { newDate ->
                viewModel.toggleCalendar(false)
                viewModel.loadTransactionsForDate(newDate)
            },
            onDismiss = { viewModel.toggleCalendar(false) }
        )
    }
}