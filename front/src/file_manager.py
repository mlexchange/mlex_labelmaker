import os 
import pathlib
import copy

def move_a_file(source, destination):
    '''
    Args:
        source, str:          full path of a file from source directory
        destination, str:     full path of destination directory 
    '''
    pathlib.Path(destination).mkdir(parents=True, exist_ok=True)
    filename = source.split('/')[-1]
    new_destination = destination + '/' + filename
    os.rename(source, new_destination)

def move_dir(source, destination):
    '''
    Args:
        source, str:          full path of source directory
        destination, str:     full path of destination directory 
    '''
    dir_path, list_dirs, filenames = next(os.walk(source))
    original_dir_name = dir_path.split('/')[-1]
    destination = destination + '/' + original_dir_name
    pathlib.Path(destination).mkdir(parents=True, exist_ok=True)
    for filename in filenames:
        file_source = dir_path + '/' + filename  
        move_a_file(file_source, destination)
    
    for dirname in list_dirs:
        dir_source = dir_path + '/' + dirname
        move_dir(dir_source, destination)


def add_paths_from_dir(dir_path, supported_formats, list_file_path):
    '''
    Args:
        dir_path, str:            full path of a directory
        supported_formats, list:  supported formats, e.g., ['tiff', 'tif', 'jpg', 'jpeg', 'png']
        list_file_path, [str]:     list of absolute file paths
    
    Returns:
        Adding unique file paths to list_file_path, [str]
    '''
    hidden_formats = ['DS_Store']
    root_path, list_dirs, filenames = next(os.walk(dir_path))
    for filename in filenames:
        exts = filename.split('.')
        if exts[-1] in supported_formats and exts[-1] not in hidden_formats and exts[-2] != '':
            file_path = root_path + '/' + filename
            if file_path not in list_file_path:
                list_file_path.append(file_path)
            
    for dirname in list_dirs:
        new_dir_path = dir_path + '/' + dirname
        list_file_path = add_paths_from_dir(new_dir_path, supported_formats, list_file_path)
    
    return list_file_path


def filename_list(directory, format):
    '''
    Args:
        directory, str:     full path of a directory
        format, list(str):  list of supported formats
    Return:
        a full list of absolute file path (filtered by file formats) inside a directory. 
    '''
    hidden_formats = ['DS_Store']
    files = []
    if format == 'dir':
        if os.path.exists(directory):
            for filepath in pathlib.Path(directory).glob('**/*'):
                if os.path.isdir(filepath):
                    files.append({'file_path': str(filepath.absolute()), 'file_type': 'dir'})
    else:
        format = format.split(',')
        for f_ext in format:
            if os.path.exists(directory):
                for filepath in pathlib.Path(directory).glob('**/{}'.format(f_ext)):
                    if os.path.isdir(filepath):
                        files.append({'file_path': str(filepath.absolute()), 'file_type': 'dir'})
                    else:
                        filename = str(filepath).split('/')[-1]
                        exts = filename.split('.')
                        if exts[-1] not in hidden_formats and exts[-2] != '':
                            files.append({'file_path': str(filepath.absolute()), 'file_type': 'file'})
    
    return files


def check_duplicate_filename(dir_path, filename):
    root_path, list_dirs, filenames = next(os.walk(dir_path))
    if filename in filenames:
        return True
    else:
        return False


def docker_to_local_path(paths, docker_home, local_home, type='list-dict'):
    '''
    Args:
        paths:              docker file paths
        docker_home, str:   full path of home dir (ends with '/') in docker environment
        local_home, str:    full path of home dir (ends with '/') mounted in local machine
        type:
            list-dict, default:  a list of dictionary (docker paths), e.g., [{'file_path': 'docker_path1'},{...}]
    Return: 
        replace docker path with local path.
    '''
    files = copy.deepcopy(paths)
    for file in files:
        if not file['file_path'].startswith(local_home):
            file['file_path'] = local_home + file['file_path'].split(docker_home)[-1]
    
    return files


def local_to_docker_path(paths, docker_home, local_home, type='dict-list'):
    '''
    Args:
        paths:             selected local (full) paths 
        docker_home, str:  full path of home dir (ends with '/') in docker environment
        local_home, str:   full path of home dir (ends with '/') mounted in local machine
        type:
            dict-list, default:  local paths wrt label class, e.g., {'1': ['selected_card_path1', 'selected_card_path2'], ...} 
            str:                 single path string 
            list:                a list of path string
            
    Return: 
        replace local path with docker path
    '''
    if type == 'dict-list':
        files = copy.deepcopy(paths)
        for key, value_list in files.items():
            new_value_list = []
            for value in value_list:
                if not value.startswith(docker_home):
                    new_value_list.append(docker_home + value.split(local_home)[-1])
                else:
                    new_value_list.append(value)
       
            files[key] = new_value_list
    
    if type == 'str':
        if not paths.startswith(docker_home):
            files = docker_home + paths.split(local_home)[-1]
        else:
            files = paths
    
    if type == 'list':
        files = []
        for i in range(len(paths)):
            if not paths[i].startswith(docker_home):
                files.append(docker_home + paths[i].split(local_home)[-1])
            else:
                files.append(paths[i])

    return files



