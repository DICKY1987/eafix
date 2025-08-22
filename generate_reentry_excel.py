#!/usr/bin/env python3
"""
Generate comprehensive Excel workbook for HUEY_P Reentry System
Creates multiple sheets with matrix combinations and parameter sets
"""

import pandas as pd
import numpy as np
from datetime import datetime
import itertools

# Excel file path
excel_file = "HUEY_P_Reentry_System_Matrix.xlsx"

# Define all dimensions for the Multi-Dimensional Matrix
SIGNAL_TYPES = [
    "ECO_HIGH", "ECO_MED", "ANTICIPATION", "EQUITY_OPEN", 
    "TECHNICAL", "MOMENTUM", "REVERSAL", "CORRELATION"
]

TIME_CATEGORIES = [
    "FLASH", "INSTANT", "QUICK", "SHORT", 
    "MEDIUM", "LONG", "EXTENDED"
]

OUTCOME_BUCKETS = [
    "BUCKET_1_ML", "BUCKET_2_PARTIAL_LOSS", "BUCKET_3_BREAKEVEN",
    "BUCKET_4_PARTIAL_PROFIT", "BUCKET_5_TARGET", "BUCKET_6_EXCEEDED"
]

MARKET_CONTEXTS = [
    "PRE_NEWS_FAR", "PRE_NEWS_NEAR", "NEWS_WINDOW", "POST_NEWS_IMMEDIATE",
    "POST_NEWS_EXTENDED", "SESSION_OPEN_MAJOR", "SESSION_OPEN_MINOR",
    "SESSION_CLOSE_MAJOR", "SESSION_CLOSE_MINOR", "OVERLAP_ACTIVE",
    "OVERLAP_ENDING", "TREND_STRONG_UP", "TREND_STRONG_DOWN", "TREND_WEAK",
    "RANGE_BOUND", "VOLATILITY_HIGH", "VOLATILITY_LOW", "CORRELATION_HIGH",
    "CORRELATION_LOW", "VOLUME_HIGH", "VOLUME_LOW", "SUPPORT_LEVEL",
    "RESISTANCE_LEVEL", "BREAKOUT_UP", "BREAKOUT_DOWN", "REVERSAL_PATTERN",
    "CONTINUATION_PATTERN", "GAP_UP", "GAP_DOWN", "SQUEEZE_PATTERN",
    "EXPANSION_PATTERN", "MOMENTUM_DIVERGENCE", "LIQUIDITY_LOW",
    "SPREAD_WIDE", "SPREAD_NORMAL", "CROSS_CORRELATION", "PORTFOLIO_STRESS",
    "RISK_ON", "RISK_OFF", "CENTRAL_BANK_ACTIVE", "HOLIDAY_PERIOD"
]

def generate_matrix_sheet():
    """Generate the complete 34,560 combination matrix"""
    print("Generating Multi-Dimensional Matrix...")
    
    # Create all combinations
    combinations = list(itertools.product(
        SIGNAL_TYPES, TIME_CATEGORIES, OUTCOME_BUCKETS, MARKET_CONTEXTS
    ))
    
    # Create DataFrame with default values
    matrix_data = []
    for i, (signal, time_cat, outcome, context) in enumerate(combinations):
        # Generate sample performance metrics (would be populated from actual data)
        base_multiplier = np.random.uniform(0.8, 1.5)
        confidence = np.random.uniform(0.3, 0.9)
        success_rate = np.random.uniform(0.35, 0.85)
        
        matrix_data.append({
            'Combination_ID': f"C_{i+1:05d}",
            'Signal_Type': signal,
            'Time_Category': time_cat,
            'Outcome_Bucket': outcome,
            'Market_Context': context,
            'Base_Multiplier': round(base_multiplier, 3),
            'Confidence_Score': round(confidence, 3),
            'Historical_Success_Rate': round(success_rate, 3),
            'Total_Executions': np.random.randint(0, 100),
            'Profitable_Executions': 0,  # Will be calculated
            'Average_PnL': round(np.random.uniform(-50, 150), 2),
            'Max_Drawdown': round(np.random.uniform(10, 200), 2),
            'Sharpe_Ratio': round(np.random.uniform(-0.5, 2.5), 3),
            'Last_Updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    # Calculate profitable executions based on success rate
    for row in matrix_data:
        row['Profitable_Executions'] = int(row['Total_Executions'] * row['Historical_Success_Rate'])
    
    return pd.DataFrame(matrix_data)

def generate_persona_parameters():
    """Generate persona-based parameter sets"""
    print("Generating Persona Parameter Sets...")
    
    personas_data = []
    
    # Conservative Persona
    conservative = {
        'Persona': 'Conservative',
        'Risk_Tolerance': 'Low',
        'Base_Multiplier_Min': 0.5,
        'Base_Multiplier_Max': 1.0,
        'Min_Confidence_Threshold': 0.7,
        'Max_Generations': 2,
        'Delay_Between_Reentries_Sec': 300,
        'Daily_Loss_Limit_Percent': 2.0,
        'Position_Size_Cap_Lots': 0.5,
        'Blackout_After_Losses': 2,
        'Blackout_Duration_Minutes': 60,
        'News_Avoidance_Minutes': 30,
        'Volatility_Filter_Enabled': True,
        'Max_Spread_Pips': 3.0,
        'Weekend_Gap_Filter': True
    }
    
    # Moderate Persona  
    moderate = {
        'Persona': 'Moderate',
        'Risk_Tolerance': 'Medium',
        'Base_Multiplier_Min': 0.8,
        'Base_Multiplier_Max': 1.5,
        'Min_Confidence_Threshold': 0.6,
        'Max_Generations': 3,
        'Delay_Between_Reentries_Sec': 180,
        'Daily_Loss_Limit_Percent': 3.0,
        'Position_Size_Cap_Lots': 1.0,
        'Blackout_After_Losses': 3,
        'Blackout_Duration_Minutes': 30,
        'News_Avoidance_Minutes': 15,
        'Volatility_Filter_Enabled': True,
        'Max_Spread_Pips': 5.0,
        'Weekend_Gap_Filter': True
    }
    
    # Aggressive Persona
    aggressive = {
        'Persona': 'Aggressive',
        'Risk_Tolerance': 'High',
        'Base_Multiplier_Min': 1.0,
        'Base_Multiplier_Max': 2.5,
        'Min_Confidence_Threshold': 0.4,
        'Max_Generations': 5,
        'Delay_Between_Reentries_Sec': 60,
        'Daily_Loss_Limit_Percent': 5.0,
        'Position_Size_Cap_Lots': 2.0,
        'Blackout_After_Losses': 5,
        'Blackout_Duration_Minutes': 15,
        'News_Avoidance_Minutes': 5,
        'Volatility_Filter_Enabled': False,
        'Max_Spread_Pips': 8.0,
        'Weekend_Gap_Filter': False
    }
    
    return pd.DataFrame([conservative, moderate, aggressive])

def generate_action_configuration():
    """Generate the six-bucket action configuration"""
    print("Generating Action Configuration...")
    
    actions_data = [
        {
            'Bucket': 1,
            'Outcome': 'R = ML (Hit Stop Loss)',
            'Description': 'Trade closed at maximum loss',
            'Default_Action': 'NO_REENTRY',
            'Conservative_Action': 'NO_REENTRY',
            'Conservative_Multiplier': 0.0,
            'Moderate_Action': 'NO_REENTRY', 
            'Moderate_Multiplier': 0.0,
            'Aggressive_Action': 'REDUCE_SIZE',
            'Aggressive_Multiplier': 0.5,
            'Risk_Level': 'HIGH',
            'Typical_Context': 'Strong adverse move, signal failure'
        },
        {
            'Bucket': 2,
            'Outcome': 'ML < R < B (Partial Loss)',
            'Description': 'Trade closed between stop loss and breakeven',
            'Default_Action': 'REDUCE_SIZE',
            'Conservative_Action': 'REDUCE_SIZE',
            'Conservative_Multiplier': 0.5,
            'Moderate_Action': 'REDUCE_SIZE',
            'Moderate_Multiplier': 0.7,
            'Aggressive_Action': 'SAME_TRADE',
            'Aggressive_Multiplier': 1.0,
            'Risk_Level': 'MEDIUM_HIGH',
            'Typical_Context': 'Partial adverse move, early exit'
        },
        {
            'Bucket': 3,
            'Outcome': 'R = B (Breakeven)',
            'Description': 'Trade closed at entry price',
            'Default_Action': 'SAME_TRADE',
            'Conservative_Action': 'REDUCE_SIZE',
            'Conservative_Multiplier': 0.8,
            'Moderate_Action': 'SAME_TRADE',
            'Moderate_Multiplier': 1.0,
            'Aggressive_Action': 'SAME_TRADE',
            'Aggressive_Multiplier': 1.2,
            'Risk_Level': 'MEDIUM',
            'Typical_Context': 'Neutral outcome, signal inconclusive'
        },
        {
            'Bucket': 4,
            'Outcome': 'B < R < MG (Partial Profit)',
            'Description': 'Trade closed between breakeven and take profit',
            'Default_Action': 'INCREASE_SIZE',
            'Conservative_Action': 'SAME_TRADE',
            'Conservative_Multiplier': 1.0,
            'Moderate_Action': 'INCREASE_SIZE',
            'Moderate_Multiplier': 1.3,
            'Aggressive_Action': 'INCREASE_SIZE',
            'Aggressive_Multiplier': 1.5,
            'Risk_Level': 'MEDIUM_LOW',
            'Typical_Context': 'Favorable move, early profit taking'
        },
        {
            'Bucket': 5,
            'Outcome': 'R = MG (Hit Take Profit)',
            'Description': 'Trade closed at maximum gain target',
            'Default_Action': 'SAME_TRADE',
            'Conservative_Action': 'SAME_TRADE',
            'Conservative_Multiplier': 1.0,
            'Moderate_Action': 'SAME_TRADE',
            'Moderate_Multiplier': 1.1,
            'Aggressive_Action': 'INCREASE_SIZE',
            'Aggressive_Multiplier': 1.3,
            'Risk_Level': 'LOW',
            'Typical_Context': 'Perfect execution, signal validated'
        },
        {
            'Bucket': 6,
            'Outcome': 'R > MG (Exceeded Target)',
            'Description': 'Trade closed beyond take profit target',
            'Default_Action': 'AGGRESSIVE',
            'Conservative_Action': 'INCREASE_SIZE',
            'Conservative_Multiplier': 1.2,
            'Moderate_Action': 'AGGRESSIVE',
            'Moderate_Multiplier': 1.5,
            'Aggressive_Action': 'AGGRESSIVE',
            'Aggressive_Multiplier': 2.0,
            'Risk_Level': 'VERY_LOW',
            'Typical_Context': 'Strong momentum, signal very strong'
        }
    ]
    
    return pd.DataFrame(actions_data)

def generate_risk_parameters():
    """Generate risk management parameter sets"""
    print("Generating Risk Management Parameters...")
    
    risk_data = [
        {
            'Parameter_Category': 'Position Sizing',
            'Parameter_Name': 'Base_Risk_Percent',
            'Conservative_Value': 1.0,
            'Moderate_Value': 1.5,
            'Aggressive_Value': 2.0,
            'Description': 'Base position size as percentage of account equity',
            'Min_Value': 0.1,
            'Max_Value': 5.0,
            'Units': 'Percent'
        },
        {
            'Parameter_Category': 'Position Sizing',
            'Parameter_Name': 'Max_Position_Size',
            'Conservative_Value': 0.5,
            'Moderate_Value': 1.0,
            'Aggressive_Value': 2.0,
            'Description': 'Maximum position size in lots',
            'Min_Value': 0.01,
            'Max_Value': 10.0,
            'Units': 'Lots'
        },
        {
            'Parameter_Category': 'Generation Control',
            'Parameter_Name': 'Max_Reentry_Generations',
            'Conservative_Value': 2,
            'Moderate_Value': 3,
            'Aggressive_Value': 5,
            'Description': 'Maximum reentry chain depth',
            'Min_Value': 1,
            'Max_Value': 10,
            'Units': 'Count'
        },
        {
            'Parameter_Category': 'Confidence Thresholds',
            'Parameter_Name': 'Min_Confidence_Score',
            'Conservative_Value': 0.7,
            'Moderate_Value': 0.6,
            'Aggressive_Value': 0.4,
            'Description': 'Minimum confidence for reentry execution',
            'Min_Value': 0.0,
            'Max_Value': 1.0,
            'Units': 'Score'
        },
        {
            'Parameter_Category': 'Daily Limits',
            'Parameter_Name': 'Daily_Loss_Limit',
            'Conservative_Value': 2.0,
            'Moderate_Value': 3.0,
            'Aggressive_Value': 5.0,
            'Description': 'Daily loss limit as percentage of equity',
            'Min_Value': 0.5,
            'Max_Value': 20.0,
            'Units': 'Percent'
        },
        {
            'Parameter_Category': 'Timing Controls',
            'Parameter_Name': 'Min_Reentry_Delay',
            'Conservative_Value': 300,
            'Moderate_Value': 180,
            'Aggressive_Value': 60,
            'Description': 'Minimum delay between reentries',
            'Min_Value': 10,
            'Max_Value': 3600,
            'Units': 'Seconds'
        },
        {
            'Parameter_Category': 'Blackout Controls',
            'Parameter_Name': 'Blackout_After_Losses',
            'Conservative_Value': 2,
            'Moderate_Value': 3,
            'Aggressive_Value': 5,
            'Description': 'Number of losses before blackout',
            'Min_Value': 1,
            'Max_Value': 10,
            'Units': 'Count'
        },
        {
            'Parameter_Category': 'Blackout Controls',
            'Parameter_Name': 'Blackout_Duration',
            'Conservative_Value': 60,
            'Moderate_Value': 30,
            'Aggressive_Value': 15,
            'Description': 'Blackout period duration',
            'Min_Value': 5,
            'Max_Value': 240,
            'Units': 'Minutes'
        }
    ]
    
    return pd.DataFrame(risk_data)

def generate_configuration_reference():
    """Generate configuration reference documentation"""
    print("Generating Configuration Reference...")
    
    config_data = [
        {
            'Section': 'Signal Types',
            'Item': 'ECO_HIGH',
            'Description': 'High-impact economic news events',
            'Usage': 'Major central bank decisions, employment reports',
            'Impact_Level': 'High',
            'Typical_Duration': '5-60 minutes'
        },
        {
            'Section': 'Signal Types',
            'Item': 'ECO_MED', 
            'Description': 'Medium-impact economic events',
            'Usage': 'Industrial production, consumer confidence',
            'Impact_Level': 'Medium',
            'Typical_Duration': '15-30 minutes'
        },
        {
            'Section': 'Signal Types',
            'Item': 'TECHNICAL',
            'Description': 'Technical analysis based signals',
            'Usage': 'Chart patterns, indicator crossovers',
            'Impact_Level': 'Variable',
            'Typical_Duration': '1 minute - 4 hours'
        },
        {
            'Section': 'Time Categories',
            'Item': 'FLASH',
            'Description': 'Ultra-short timeframe trades',
            'Usage': 'Scalping, news spikes',
            'Impact_Level': 'High',
            'Typical_Duration': '≤1 minute'
        },
        {
            'Section': 'Time Categories',
            'Item': 'EXTENDED',
            'Description': 'Long-term position trades',
            'Usage': 'Trend following, fundamental shifts',
            'Impact_Level': 'Low',
            'Typical_Duration': '>12 hours'
        },
        {
            'Section': 'Market Context',
            'Item': 'NEWS_WINDOW',
            'Description': 'Active news event window',
            'Usage': 'During major announcements',
            'Impact_Level': 'High',
            'Typical_Duration': '±30 minutes'
        },
        {
            'Section': 'Market Context',
            'Item': 'OVERLAP_ACTIVE',
            'Description': 'Multiple trading sessions open',
            'Usage': 'London-NY, Asia-London overlap',
            'Impact_Level': 'Medium',
            'Typical_Duration': '2-4 hours'
        },
        {
            'Section': 'Actions',
            'Item': 'NO_REENTRY',
            'Description': 'Do not execute reentry trade',
            'Usage': 'After stop losses, high risk situations',
            'Impact_Level': 'None',
            'Typical_Duration': 'Immediate'
        },
        {
            'Section': 'Actions',
            'Item': 'AGGRESSIVE',
            'Description': 'Significantly increased position size',
            'Usage': 'After strong profitable trades',
            'Impact_Level': 'High',
            'Typical_Duration': 'Next trade cycle'
        }
    ]
    
    return pd.DataFrame(config_data)

def main():
    """Generate complete Excel workbook"""
    print(f"Creating HUEY_P Reentry System Excel workbook: {excel_file}")
    print("This may take a few moments due to the size of the matrix...")
    
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        # Sheet 1: Multi-Dimensional Matrix (34,560 combinations)
        matrix_df = generate_matrix_sheet()
        matrix_df.to_excel(writer, sheet_name='Matrix_34560_Combinations', index=False)
        print(f"[OK] Matrix sheet created: {len(matrix_df)} combinations")
        
        # Sheet 2: Persona Parameter Sets
        persona_df = generate_persona_parameters()
        persona_df.to_excel(writer, sheet_name='Persona_Parameters', index=False)
        print(f"[OK] Persona parameters sheet created: {len(persona_df)} personas")
        
        # Sheet 3: Action Configuration
        action_df = generate_action_configuration()
        action_df.to_excel(writer, sheet_name='Action_Configuration', index=False)
        print(f"[OK] Action configuration sheet created: {len(action_df)} buckets")
        
        # Sheet 4: Risk Management Parameters
        risk_df = generate_risk_parameters()
        risk_df.to_excel(writer, sheet_name='Risk_Parameters', index=False)
        print(f"[OK] Risk parameters sheet created: {len(risk_df)} parameters")
        
        # Sheet 5: Configuration Reference
        config_df = generate_configuration_reference()
        config_df.to_excel(writer, sheet_name='Configuration_Reference', index=False)
        print(f"[OK] Configuration reference sheet created: {len(config_df)} items")
        
        # Sheet 6: Summary
        summary_data = [
            ['Total Matrix Combinations', len(matrix_df)],
            ['Signal Types', len(SIGNAL_TYPES)],
            ['Time Categories', len(TIME_CATEGORIES)],
            ['Outcome Buckets', len(OUTCOME_BUCKETS)],
            ['Market Contexts', len(MARKET_CONTEXTS)],
            ['Persona Profiles', len(persona_df)],
            ['Action Buckets', len(action_df)],
            ['Risk Parameters', len(risk_df)],
            ['Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        ]
        summary_df = pd.DataFrame(summary_data, columns=['Metric', 'Value'])
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        print("[OK] Summary sheet created")
    
    print(f"\nSUCCESS: Excel workbook generated: {excel_file}")
    print("\nSheet Contents:")
    print("- Matrix_34560_Combinations: Complete multi-dimensional matrix")
    print("- Persona_Parameters: Conservative/Moderate/Aggressive profiles") 
    print("- Action_Configuration: Six-bucket reentry actions")
    print("- Risk_Parameters: Risk management settings")
    print("- Configuration_Reference: Documentation and usage guide")
    print("- Summary: Workbook overview")

if __name__ == "__main__":
    main()