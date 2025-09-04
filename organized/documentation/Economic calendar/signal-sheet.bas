[Option Explicit]

Sub CreateSignalParametersWorksheet()
    ' Create a Signal Parameters configuration worksheet
    ' This sheet allows detailed configuration of various signal types
    
    Application.ScreenUpdating = False
    Application.DisplayAlerts = False
    
    ' Check if sheet already exists, if so, delete it
    Dim ws As Worksheet
    On Error Resume Next
    Set ws = ThisWorkbook.Sheets("Signal Parameters")
    On Error GoTo 0
    
    If Not ws Is Nothing Then
        ws.Delete
    End If
    
    ' Create new sheet
    Set ws = ThisWorkbook.Sheets.Add(After:=ThisWorkbook.Sheets(ThisWorkbook.Sheets.Count))
    ws.Name = "Signal Parameters"
    
    ' Set column widths
    ws.Columns("A").ColumnWidth = 25
    ws.Columns("B").ColumnWidth = 30
    ws.Columns("C").ColumnWidth = 35
    ws.Columns("D").ColumnWidth = 15
    
    ' Add title
    ws.Range("A1").Value = "SIGNAL PARAMETERS CONFIGURATION"
    ws.Range("A1").Font.Size = 14
    ws.Range("A1").Font.Bold = True
    
    ' Signal Type selection section
    ws.Range("A3").Value = "SIGNAL TYPE SELECTION"
    ws.Range("A3").Font.Bold = True
    ws.Range("A3:C3").Interior.Color = RGB(200, 220, 255)
    
    ' Add field labels
    ws.Range("A4").Value = "Signal Category"
    ws.Range("A5").Value = "Signal Type"
    ws.Range("A6").Value = "Signal Logic ID"
    
    ' Add field descriptions
    ws.Range("C4").Value = "General category of signal (Technical, Fundamental, etc.)"
    ws.Range("C5").Value = "Specific signal type within the category"
    ws.Range("C6").Value = "Unique ID for this signal configuration"
    
    ' Signal Parameters section
    ws.Range("A8").Value = "SIGNAL PARAMETERS"
    ws.Range("A8").Font.Bold = True
    ws.Range("A8:D8").Interior.Color = RGB(200, 220, 255)
    
    ' Parameter headers
    ws.Range("A9").Value = "Parameter"
    ws.Range("B9").Value = "Value"
    ws.Range("C9").Value = "Description"
    ws.Range("D9").Value = "Required"
    
    ws.Range("A9:D9").Font.Bold = True
    ws.Range("A9:D9").Interior.Color = RGB(240, 240, 240)
    
    ' Dynamic parameter section - this will be populated when a signal type is selected
    
    ' Signal Testing section
    ws.Range("A25").Value = "SIGNAL TESTING"
    ws.Range("A25").Font.Bold = True
    ws.Range("A25:D25").Interior.Color = RGB(200, 220, 255)
    
    ' Testing fields
    ws.Range("A26").Value = "Test Period Start"
    ws.Range("A27").Value = "Test Period End"
    ws.Range("A28").Value = "Back-testing Win Rate"
    ws.Range("A29").Value = "Average Signal Quality"
    
    ' Testing field descriptions
    ws.Range("C26").Value = "Start date for signal back-testing"
    ws.Range("C27").Value = "End date for signal back-testing"
    ws.Range("C28").Value = "Percentage of successful signals in testing"
    ws.Range("C29").Value = "Quality score (0-100) based on signal metrics"
    
    ' Signal Confirmation section
    ws.Range("A31").Value = "SIGNAL CONFIRMATION"
    ws.Range("A31").Font.Bold = True
    ws.Range("A31:D31").Interior.Color = RGB(200, 220, 255)
    
    ' Confirmation fields
    ws.Range("A32").Value = "Confirmation Required"
    ws.Range("A33").Value = "Confirmation Signal Type"
    ws.Range("A34").Value = "Confirmation Logic"
    
    ' Confirmation field descriptions
    ws.Range("C32").Value = "Require confirmation from another signal?"
    ws.Range("C33").Value = "Type of signal used for confirmation"
    ws.Range("C34").Value = "Logical relationship (AND, OR, FOLLOWS, etc.)"
    
    ' Add data validation for dropdown fields
    
    ' Signal Category dropdown
    ws.Range("B4").Validation.Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, _
        Formula1:="Technical,Fundamental,Statistical,Behavioral,Pattern,Hybrid"
    
    ' Signal Type will be populated dynamically based on category
    
    ' Confirmation Required dropdown
    ws.Range("B32").Validation.Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, _
        Formula1:="Yes,No"
    
    ' Confirmation Logic dropdown
    ws.Range("B34").Validation.Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, _
        Formula1:="AND,OR,FOLLOWS,NEGATES,STRENGTHENS"
    
    ' Add function buttons
    AddSignalParameterButtons ws
    
    ' Add test data for demonstration
    AddSampleSignalData ws
    
    ' Add event handling
    SetupSignalParameterEvents ws
    
    ' Format borders
    ws.Range("A3:C6").Borders.LineStyle = xlContinuous
    ws.Range("A8:D20").Borders.LineStyle = xlContinuous
    ws.Range("A25:D29").Borders.LineStyle = xlContinuous
    ws.Range("A31:D34").Borders.LineStyle = xlContinuous
    
    ' Select the first sheet
    ws.Select
    ws.Range("A1").Select
    
    Application.ScreenUpdating = True
    Application.DisplayAlerts = True
    
    MsgBox "Signal Parameters worksheet created successfully!", vbInformation
End Sub

Sub AddSignalParameterButtons(ws As Worksheet)
    ' Add buttons for managing signal parameters
    
    ' Save Configuration button
    ws.Shapes.AddShape(msoShapeRoundedRectangle, 300, 400, 150, 30).Select
    With Selection
        .Characters.Text = "Save Configuration"
        .ShapeRange.Fill.ForeColor.RGB = RGB(0, 176, 80)
        .ShapeRange.TextFrame2.TextRange.Font.Size = 10
        .ShapeRange.TextFrame2.TextRange.Font.Fill.ForeColor.RGB = RGB(255, 255, 255)
        .ShapeRange.Name = "SaveSignalConfig"
        .OnAction = "SaveSignalConfiguration"
    End With
    
    ' Test Signal button
    ws.Shapes.AddShape(msoShapeRoundedRectangle, 470, 400, 150, 30).Select
    With Selection
        .Characters.Text = "Test Signal"
        .ShapeRange.Fill.ForeColor.RGB = RGB(0, 112, 192)
        .ShapeRange.TextFrame2.TextRange.Font.Size = 10
        .ShapeRange.TextFrame2.TextRange.Font.Fill.ForeColor.RGB = RGB(255, 255, 255)
        .ShapeRange.Name = "TestSignal"
        .OnAction = "TestSignalConfiguration"
    End With
    
    ' Load Configuration button
    ws.Shapes.AddShape(msoShapeRoundedRectangle, 130, 400, 150, 30).Select
    With Selection
        .Characters.Text = "Load Configuration"
        .ShapeRange.Fill.ForeColor.RGB = RGB(112, 48, 160)
        .ShapeRange.TextFrame2.TextRange.Font.Size = 10
        .ShapeRange.TextFrame2.TextRange.Font.Fill.ForeColor.RGB = RGB(255, 255, 255)
        .ShapeRange.Name = "LoadSignalConfig"
        .OnAction = "LoadSignalConfiguration"
    End With
    
    ' Add to Strategy button
    ws.Shapes.AddShape(msoShapeRoundedRectangle, 300, 450, 150, 30).Select
    With Selection
        .Characters.Text = "Add to Strategy"
        .ShapeRange.Fill.ForeColor.RGB = RGB(255, 128, 0)
        .ShapeRange.TextFrame2.TextRange.Font.Size = 10
        .ShapeRange.TextFrame2.TextRange.Font.Fill.ForeColor.RGB = RGB(255, 255, 255)
        .ShapeRange.Name = "AddToStrategy"
        .OnAction = "AddSignalToStrategy"
    End With
End Sub

Sub AddSampleSignalData(ws As Worksheet)
    ' Add sample signal parameter data for demonstration
    
    ' Set sample values
    ws.Range("B4").Value = "Technical"
    ws.Range("B5").Value = "Moving Average Crossovers"
    ws.Range("B6").Value = "MAC-001"
    
    ' Sample parameter values
    ws.Range("A10").Value = "Fast MA Period"
    ws.Range("B10").Value = "10"
    ws.Range("C10").Value = "Period for the fast moving average"
    ws.Range("D10").Value = "Yes"
    
    ws.Range("A11").Value = "Slow MA Period"
    ws.Range("B11").Value = "20"
    ws.Range("C11").Value = "Period for the slow moving average"
    ws.Range("D11").Value = "Yes"
    
    ws.Range("A12").Value = "MA Type"
    ws.Range("B12").Value = "EMA"
    ws.Range("C12").Value = "Type of moving average (SMA, EMA, WMA, etc.)"
    ws.Range("D12").Value = "Yes"
    
    ws.Range("A13").Value = "Price Type"
    ws.Range("B13").Value = "Close"
    ws.Range("C13").Value = "Price data to use (Open, High, Low, Close)"
    ws.Range("D13").Value = "Yes"
    
    ws.Range("A14").Value = "Cross Direction"
    ws.Range("B14").Value = "Fast Above Slow"
    ws.Range("C14").Value = "Direction of crossover that generates signal"
    ws.Range("D14").Value = "Yes"
    
    ws.Range("A15").Value = "Minimum Slope"
    ws.Range("B15").Value = "0.001"
    ws.Range("C15").Value = "Minimum slope of fast MA for valid signal"
    ws.Range("D15").Value = "No"
    
    ws.Range("A16").Value = "Volume Confirmation"
    ws.Range("B16").Value = "Yes"
    ws.Range("C16").Value = "Require above-average volume with signal"
    ws.Range("D16").Value = "No"
    
    ' Test data
    ws.Range("B26").Value = "2025-01-01"
    ws.Range("B27").Value = "2025-03-31"
    ws.Range("B28").Value = "68.5%"
    ws.Range("B29").Value = "75"
    
    ' Confirmation data
    ws.Range("B32").Value = "Yes"
    ws.Range("B33").Value = "RSI Overbought/Oversold"
    ws.Range("B34").Value = "AND"
End Sub

Sub SetupSignalParameterEvents(ws As Worksheet)
    ' This would set up worksheet events for the Signal Parameters sheet
    ' In a real implementation, you would add a Worksheet_Change event to the sheet
    ' For this example, we'll just add a note
    
    Dim note As String
    note = "In a real implementation, you would add code to the Worksheet_Change event to:"
    note = note & vbCrLf & "1. Update signal type dropdown when category changes"
    note = note & vbCrLf & "2. Update parameter fields when signal type changes"
    note = note & vbCrLf & "3. Handle confirmation signal type dropdown when confirmation is required"
    
    ws.Range("A36").Value = note
    ws.Range("A36").Font.Italic = True
    
    ' For demo purposes, we'll populate the Signal Type dropdown based on the sample value in B4
    PopulateSignalTypesForCategory ws, ws.Range("B4").Value
End Sub

Sub PopulateSignalTypesForCategory(ws As Worksheet, category As String)
    ' Populate the Signal Type dropdown based on selected category
    
    Dim signalTypes As String
    
    Select Case category
        Case "Technical"
            signalTypes = "Moving Average Crossovers,RSI Overbought/Oversold,MACD Crossovers,Bollinger Band Bounces/Breakouts,Stochastic Crossovers,ADX Trend Strength"
        
        Case "Fundamental"
            signalTypes = "Earnings Reports Reaction,Geopolitical or Macroeconomic Event Signal,Scheduled Event Triggers,Economic Data Releases"
        
        Case "Statistical"
            signalTypes = "Statistical Arbitrage (Pairs Trading),Machine Learning Predictions,Fractal or Multi-Timeframe Confirmations"
        
        Case "Behavioral"
            signalTypes = "Sentiment Data Signals,COT Report Signals,Behavioral Sentiment Reversals,Order Book Imbalance Signals"
        
        Case "Pattern"
            signalTypes = "Candlestick Patterns,Chart Patterns,Support/Resistance Breaks,Divergence (Price vs Oscillator)"
        
        Case "Hybrid"
            signalTypes = "Multi-Indicator Confirmations,Trend-Following Signal,Reversal Signals,Breakout Signals,Range-Bound Signals"
        
        Case Else
            signalTypes = "Select a category first"
    End Select
    
    ' Apply validation list
    ws.Range("B5").Validation.Delete
    ws.Range("B5").Validation.Add Type:=xlValidateList, AlertStyle:=xlValidAlertStop, Formula1:=signalTypes
End Sub

Sub SaveSignalConfiguration()
    ' Save the current signal configuration to the database
    ' In a real implementation, this would save to a sheet or JSON file
    
    ' Get the Signal Parameters sheet
    Dim ws As Worksheet
    On Error Resume Next
    Set ws = ThisWorkbook.Sheets("Signal Parameters")
    On Error GoTo 0
    
    If ws Is Nothing Then
        MsgBox "Signal Parameters sheet not found.", vbExclamation
        Exit Sub
    End If
    
    ' Get the signal logic ID
    Dim signalLogicID As String
    signalLogicID = ws.Range("B6").Value
    
    If signalLogicID = "" Then
        MsgBox "Please enter a Signal Logic ID before saving.", vbExclamation
        Exit Sub
    End If
    
    ' In a real implementation, you would save the configuration to a database
    ' For this example, we'll just show a message box
    
    Dim msg As String
    msg = "Signal configuration " & signalLogicID & " would be saved to the database."
    msg = msg & vbCrLf & vbCrLf & "Signal Type: " & ws.Range("B5").Value
    msg = msg & vbCrLf & "Parameters: " & (ws.Range("A15").Row - ws.Range("A10").Row + 1) & " parameters"
    
    MsgBox msg, vbInformation
End Sub

Sub TestSignalConfiguration()
    ' Test the current signal configuration on historical data
    ' In a real implementation, this would run a backtest
    
    ' Get the Signal Parameters sheet
    Dim ws As Worksheet
    On Error Resume Next
    Set ws = ThisWorkbook.Sheets("Signal Parameters")
    On Error GoTo 0
    
    If ws Is Nothing Then
        MsgBox "Signal Parameters sheet not found.", vbExclamation
        Exit Sub
    End If
    
    ' Validate that required parameters are filled
    Dim range As Range
    Dim cell As Range
    Dim missingParams As Boolean
    
    missingParams = False
    Set range = ws.Range("A10:D16")
    
    For Each cell In range.Columns(4).Cells
        If cell.Value = "Yes" Then
            ' This is a required parameter, check if the value is filled
            If range.Cells(cell.Row - range.Row + 1, 2).Value = "" Then
                missingParams = True
                Exit For
            End If
        End If
    Next cell
    
    If missingParams Then
        MsgBox "Please fill in all required parameters before testing.", vbExclamation
        Exit Sub
    End If
    
    ' In a real implementation, you would run a backtest on historical data
    ' For this example, we'll simulate a test result
    
    ' Generate simulated test results
    Dim winRate As Double
    Dim signalQuality As Integer
    
    winRate = Int(Rnd() * 30) + 50 ' Random between 50% and 80%
    signalQuality = Int(Rnd() * 40) + 50 ' Random between 50 and 90
    
    ' Update the test results
    ws.Range("B28").Value = Format(winRate / 100, "0.0%")
    ws.Range("B29").Value = signalQuality
    
    ' Format based on quality
    If winRate >= 65 Then
        ws.Range("B28").Interior.Color = RGB(200, 255, 200) ' Green for good
    ElseIf winRate >= 55 Then
        ws.Range("B28").Interior.Color = RGB(255, 255, 200) ' Yellow for medium
    Else
        ws.Range("B28").Interior.Color = RGB(255, 200, 200) ' Red for poor
    End If
    
    If signalQuality >= 75 Then
        ws.Range("B29").Interior.Color = RGB(200, 255, 200) ' Green for good
    ElseIf signalQuality >= 60 Then
        ws.Range("B29").Interior.Color = RGB(255, 255, 200) ' Yellow for medium
    Else
        ws.Range("B29").Interior.Color = RGB(255, 200, 200) ' Red for poor
    End If
    
    MsgBox "Signal test complete!" & vbCrLf & vbCrLf & _
           "Win Rate: " & ws.Range("B28").Value & vbCrLf & _
           "Signal Quality: " & ws.Range("B29").Value, vbInformation
End Sub

Sub LoadSignalConfiguration()
    ' Load a signal configuration from the database
    ' In a real implementation, this would load from a sheet or JSON file
    
    ' This would typically show a form with a list of saved signal configurations
    ' For this example, we'll simulate loading a pre-defined configuration
    
    MsgBox "In a real implementation, this would show a list of saved signal configurations to load." & _
           vbCrLf & vbCrLf & "For this example, we'll load a sample configuration.", vbInformation
    
    ' Get the Signal Parameters sheet
    Dim ws As Worksheet
    On Error Resume Next
    Set ws = ThisWorkbook.Sheets("Signal Parameters")
    On Error GoTo 0
    
    If ws Is Nothing Then
        MsgBox "Signal Parameters sheet not found.", vbExclamation
        Exit Sub
    End If
    
    ' Load a sample RSI configuration
    ws.Range("B4").Value = "Technical"
    PopulateSignalTypesForCategory ws, "Technical"
    
    ws.Range("B5").Value = "RSI Overbought/Oversold"
    ws.Range("B6").Value = "RSI-001"
    
    ' Clear existing parameter values
    ws.Range("A10:D20").ClearContents
    
    ' Set new parameter values
    ws.Range("A10").Value = "RSI Period"
    ws.Range("B10").Value = "14"
    ws.Range("C10").Value = "Period for RSI calculation"
    ws.Range("D10").Value = "Yes"
    
    ws.Range("A11").Value = "Overbought Level"
    ws.Range("B11").Value = "70"
    ws.Range("C11").Value = "Level considered overbought"
    ws.Range("D11").Value = "Yes"
    
    ws.Range("A12").Value = "Oversold Level"
    ws.Range("B12").Value = "30"
    ws.Range("C12").Value = "Level considered oversold"
    ws.Range("D12").Value = "Yes"
    
    ws.Range("A13").Value = "Price Type"
    ws.Range("B13").Value = "Close"
    ws.Range("C13").Value = "Price data to use (Open, High, Low, Close)"
    ws.Range("D13").Value = "Yes"
    
    ws.Range("A14").Value = "Signal Mode"
    ws.Range("B14").Value = "Crosses Below Overbought"
    ws.Range("C14").Value = "How RSI generates a signal"
    ws.Range("D14").Value = "Yes"
    
    ws.Range("A15").Value = "Divergence Detection"
    ws.Range("B15").Value = "Yes"
    ws.Range("C15").Value = "Look for price-RSI divergences"
    ws.Range("D15").Value = "No"
    
    ws.Range("A16").Value = "Minimum RSI Change"
    ws.Range("B16").Value = "5"
    ws.Range("C16").Value = "Minimum change in RSI value for valid signal"
    ws.Range("D16").Value = "No"
    
    ' Test data - leave existing
    
    MsgBox "Sample RSI configuration loaded successfully!", vbInformation
End Sub

Sub AddSignalToStrategy()
    ' Add the current signal configuration to a strategy
    ' This would link a signal to a trading strategy
    
    ' Get the Signal Parameters sheet
    Dim ws As Worksheet
    On Error Resume Next
    Set ws = ThisWorkbook.Sheets("Signal Parameters")
    On Error GoTo 0
    
    If ws Is Nothing Then
        MsgBox "Signal Parameters sheet not found.", vbExclamation
        Exit Sub
    End If
    
    ' Get the signal logic ID
    Dim signalLogicID As String
    signalLogicID = ws.Range("B6").Value
    
    If signalLogicID = "" Then
        MsgBox "Please enter a Signal Logic ID before adding to a strategy.", vbExclamation
        Exit Sub
    End If
    
    ' In a real implementation, this would show a form to select a strategy
    ' For this example, we'll just show a message
    
    MsgBox "Signal " & signalLogicID & " would be added to a strategy." & vbCrLf & vbCrLf & _
           "In a real implementation, this would show a form to select a strategy from the Strategy Database.", vbInformation
    
    ' Optionally open the Trade Parameters sheet
    Dim response As VbMsgBoxResult
    response = MsgBox("Would you like to open the Trade Parameters sheet to continue strategy configuration?", _
                      vbYesNo + vbQuestion, "Open Trade Parameters")
    
    If response = vbYes Then
        ' Check if Trade Parameters sheet exists
        Dim tpSheet As Worksheet
        On Error Resume Next
        Set tpSheet = ThisWorkbook.Sheets("Trade Parameters")
        On Error GoTo 0
        
        If tpSheet Is Nothing Then
            ' Sheet doesn't exist, create it
            MsgBox "Trade Parameters sheet not found. Creating it now.", vbInformation
            Application.Run "CreateTradeParametersWorksheet"
        Else
            ' Sheet exists, activate it
            tpSheet.Activate
        End If
        
        ' In a real implementation, you would populate the signal fields
        ' in the Trade Parameters sheet with the current signal configuration
    End If
End Sub
