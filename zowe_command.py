# streamlit run main.py
import streamlit as st
import json
import subprocess
import re

st.title(f'Zowe CLI Command Builder')

st.write('Zowe CLI Command Builder')
st.write('This tool helps you build Zowe CLI commands')

if 'first_time_zowe' not in st.session_state:
    st.session_state.first_time_zowe=False
if 'first_time_zowe_create_file' not in st.session_state:
    st.session_state.first_time_zowe_create_file=False
if 'zowe_dict' not in st.session_state:
    st.session_state.zowe_dict=False
if 'zowe_command' not in st.session_state:
    st.session_state.zowe_command=''
if 'zowe_group_command' not in st.session_state:
    st.session_state.zowe_group_command='zowe'
if 'zowe_options_command' not in st.session_state:
    st.session_state.zowe_options_command=''
if 'selectb' not in st.session_state:
    st.session_state.selectb=False
if "create_button_disabled" not in st.session_state:
    st.session_state.create_button_disabled = True  # Button starts as disabled
if "submit_button_disabled" not in st.session_state:
    st.session_state.submit_button_disabled = True  # Button starts as disabled


#------------------- EXECUTE COMMAND ----------------------------------------
# args: 
#    'command'(str) command to be executed
# -----
# returns:
#    stdout
#    stderr
#    returncode  
def execute_command(command):
   try:
      result = subprocess.run(command, shell=True, text=True, capture_output=True)

   except subprocess.CalledProcessError as e:
      st.write("Command execution failed.")
      st.write("Return Code:", e.returncode)
      st.write("Error:", e.stderr)
      exit(8)

   if result.returncode!=0:
      st.write('rc', result.returncode)
      st.write('sto ', result.stdout)
      st.write('ste ', result.stderr)
      # exit(8)

   return result.stdout, result.stderr, result.returncode 
#----------------------------------------------------------------------------


#------------------- RUNS ONLY FIRST TIME -----------------------------------
#- Create json zowe --ac --rfj command
if not st.session_state.first_time_zowe_create_file:
    st.session_state.first_time_zowe_create_file=True 
    with st.spinner("Processing..."):
        sto, ste, rc = execute_command('zowe --ac --rfj > ./zowe_command_builder/zowe_full.json')
#----------------------------------------------------------------------------

#------------------- RUNS ONLY FIRST TIME OR RESET --------------------------
#- Loads json zowe --ac --rfj command
#- Creates Zowe_dict from [data]
#- Initialize Zowe command
if not st.session_state.first_time_zowe:
    st.session_state.first_time_zowe=True 
    # with open('./zowe_command_builder/zowe.json', 'r') as file:
    with open('./zowe_command_builder/zowe_full.json', 'r') as file:
        st.session_state.zowe_dict = json.load(file)
    st.session_state.zowe_dict = st.session_state.zowe_dict['data']
    st.session_state.zowe_command=''
    st.session_state.zowe_group_command='zowe'
    st.session_state.zowe_options_command=''
    st.session_state.create_button_disabled = True
#----------------------------------------------------------------------------


#------------------- LIST CHILDREN ------------------------------------------
def list_children(actions):
    for index, name in enumerate(st.session_state.zowe_dict["children"]):
        # st.write(name["name"], index)
        actions.append(name["name"])
    return actions
#----------------------------------------------------------------------------


#------------------- CREATE WIDGETS -----------------------------------------
def create_widgets(group,value):
    options_dict={}
    for item in st.session_state.zowe_dict[f'{group}']:

        if group != 'positionals':
            if item["group"]!=f'{value}':
                continue
        st.divider()

        options_dict[f'{item["name"]}'] = item["type"]
        desc = f'{item["name"]} - {item["description"]}'

        if "required" in item:
            if item["required"]:
                desc = 'Required - '+ desc
        
        if item["type"]=="boolean":
            st.toggle(f'{desc}',key=item["name"])
        
        if item["type"]=="string" or item["type"]=="number" or item["type"]=="existingLocalFile":
            # if 'allowableValues' in item:
            #     st.segmented_control(f'{desc}',item["allowableValues"]["values"],key=item["name"])
            # else:
            st.text_input(f'{desc}',key=item["name"])

    return options_dict
#----------------------------------------------------------------------------


#------------------- DISPLAY ZOWE COMMAND & RESET BUTTON --------------------
with st.container(border=True):
    colcom1, colcom2, colcom3 = st.columns([1, 5, 1], vertical_alignment="center")
    with colcom1:
        submit_button=st.button("Submit",
            type="primary",
            disabled=st.session_state.submit_button_disabled,
            )
    with colcom2:
        st.code(f"{st.session_state.zowe_command}",wrap_lines=True)
    with colcom3:
        reset=st.button('Reset',type="tertiary")
        if reset:
            st.session_state.submit_button_disabled=True
            st.session_state.first_time_zowe=False
            st.rerun()
#----------------------------------------------------------------------------


def remove_ansi_codes(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

if submit_button:
    with st.spinner("Processing..."):
        sto, ste, rc = execute_command(f'{st.session_state.zowe_command}')
        # with st.container(border=True):
        if '--rfj' in st.session_state.zowe_command or '--response-format-json' in st.session_state.zowe_command:
            lang='json'
        else:
            lang='text'
        sto = remove_ansi_codes(sto)
        with st.expander(f"Command Output",expanded=True):
            st.code(f'{sto}',wrap_lines = False, language=f'{lang}') 


#- Display selectbox with group names
if st.session_state.zowe_dict["type"] == "group":
    actions = ['-- select --']
    list_children(actions)
    # Display selectbox with group names
    st.session_state.selectb = st.selectbox("Select", actions)
    if st.session_state.selectb!='-- select --':
        st.session_state.zowe_group_command=f'{st.session_state.zowe_group_command} {st.session_state.selectb}'
        new_dict = next(
            (item for item in st.session_state.zowe_dict["children"] if item.get("name") == st.session_state.selectb),
            None  # Default value if not found
        )
        # Set the list to the found dictionary
        if new_dict:
            st.session_state.zowe_dict = new_dict
        else:
            st.warning(f"Dictionary with 'name': '{st.session_state.selectb}' not found.")
        st.session_state.zowe_command= f'{st.session_state.zowe_group_command}'
        if st.session_state.zowe_dict["type"] == "command":
            st.session_state.create_button_disabled = False
        st.rerun()

with st.form("unterse"):

#------------------- DISPLAY CREATE BUTTON ----------------------------------
    create_button=st.form_submit_button("Create Command",
        disabled=st.session_state.create_button_disabled,
        )
    # with colbut2:
    #     submit_button=st.button("Submit Command",
    #         disabled=st.session_state.submit_button_disabled,
    #         )
        
    #----------------------------------------------------------------------------


    #------------------- PROCESS ------------------------------------------------


    #- Display options for command and call set_options to create widgets
    if st.session_state.zowe_dict["type"] == "command":
        st.session_state.zowe_options_command=''
        
        #- Retrieve values from option fields
        def set_options(group,value):
            options_dict = create_widgets(f'{group}',f'{value}')
            for name, type in options_dict.items():
                if group=="positionals":
                    st.session_state.zowe_options_command=f'{st.session_state.zowe_options_command} {st.session_state.get(name)}'
                elif type=="boolean" and st.session_state.get(name) == True :
                    st.session_state.zowe_options_command=f'{st.session_state.zowe_options_command} --{name}'
                elif (type=="string" or type=="number" or type=="existingLocalFile") and st.session_state.get(name) != '':
                    # if st.session_state.get(name)==None:
                    #     st.write('Entra')
                    #     continue                
                    st.session_state.zowe_options_command=f'{st.session_state.zowe_options_command} --{name} {st.session_state.get(name)}'
                elif type not in "boolean, string, number, existingLocalFile": 
                    st.write(f'Name {name} Type {type}Not available')


        #- For each set of positionals create an expander section
        if 'positionals' in st.session_state.zowe_dict:
            if st.session_state.zowe_dict["positionals"] != []:
                positional_dict = set_options('positionals','')

        #- For each set of options create an expander section
        if 'options' in st.session_state.zowe_dict:
            if st.session_state.zowe_dict["options"] != []:
                groups = []
                options_dict={}
                for item in st.session_state.zowe_dict["options"]:
                    if "group" in item:
                        if item["group"] not in groups:
                            groups.append(item["group"])

                for options in groups:
                    with st.expander(f"{options}"):
                        options_dict = set_options('options',f'{options}')


        if 'examples' in st.session_state.zowe_dict:
            if st.session_state.zowe_dict["examples"] != []:
                with st.expander("Examples"):
                    for item in st.session_state.zowe_dict["examples"]:
                        st.write(f'{item["description"]}')
                        st.code(f'{st.session_state.zowe_group_command} {item["options"]}', wrap_lines=True)

    else:
        st.write('Not available')
        st.stop()
        exit(1)
    
    if create_button:
        st.session_state.zowe_command= f'{st.session_state.zowe_group_command} {st.session_state.zowe_options_command}'
        # Enable Command submit_button
        st.session_state.submit_button_disabled = False
        st.rerun()
    else: 
        st.session_state.submit_button_disabled = True
#----------------------------------------------------------------------------


#------------------- DISPLAY DESCRIPTION ------------------------------------
st.divider()
if st.session_state.zowe_dict["description"] != '':
    st.write(f'{st.session_state.zowe_dict["description"]}') 
st.divider()
#----------------------------------------------------------------------------