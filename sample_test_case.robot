*** Settings ***


Library           robot.libraries.DateTime

Library    ../ALMRobotListener.py

Suite Teardown  TEAR_Down


*** Variables ***
${skip_alm_post}  0  # 1=True ,0=False



*** Test Cases ***


TA_IT4_TR_504_001              # 504 is Run id in ALM   Remove this comment   TA = Test Automation , TR=Test Run
  [Tags]  noncritical
  [Documentation]  START_Execution
  Keyword1    ARGS=NONE

TA_IT4_TR_505_002       # 505 is Run id in ALM     002= Test case number
  [Tags]  noncritical
  [Documentation]  RESTART_Component
  Keyword2    

TA_IT4_TR_506_003          # 505 is Run id in ALM  --> This should match in ALM   IT4 = Integration Test no 4
  [Tags]  noncritical
  [Documentation]  VERIFY_Status_Component
  VERIFY_Keyword    EXPECTED=testing  TIMEOUT=240


  

