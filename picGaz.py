import os
import shutil
import datetime
from pathlib import Path
import hashlib
from PIL import Image
from glob import glob

from ruamel.yaml import YAML
yaml = YAML(pure=True)
yaml.sort_base_mapping_type_on_output = None
yaml.indent(mapping=2, sequence=4, offset=2)

import logging
logging.basicConfig(
    # filename= Path(__file__).parent/(Path(__file__).stem+".log"),
    level=logging.DEBUG,
    filemode='a',
    encoding='utf8',
    format='%(asctime)s - %(filename)s, line:%(lineno)d > %(levelname)s: %(message)s',
)

from traceback import format_exc


VERSION = '20221012'


def hashFile(fp, *, buffer_size=20_000_000, algorithm='md5') -> str:
    m = getattr(hashlib, algorithm)()
    file_size = os.path.getsize(fp)
    if file_size > buffer_size:
        r = 0
        with open(fp, 'rb') as f:
            while r < file_size:
                bs = f.read(buffer_size)
                m.update(bs)
                r += buffer_size
    else:
        with open(fp, 'rb') as f:
            m.update(f.read())
    return m.hexdigest()


def picExt(fn: os.PathLike) -> str:
    fn = Path(fn)
    try:
        ext = (Image.open(fn)).format
        ext = str(ext) if ext is not None else ''
        return ext
    except IOError:
        return 'picExt.IOError'


class UNIQUE_PIC_COPY():
    def __init__(self, plan: dict):
        """
        find unique pictures in the src dir(s),
        and copy them to the destination dir

        Parameters
        ----------
        plans : dict
            a configuration set from ./conf.yml
        """

        self.cfg = plan  # see the specific schema of picGaz.conf.yml samples
        self.src = Path(os.path.expanduser(self.cfg['src']))
        self.dst = Path(os.path.expanduser(self.cfg['dst']))
        self.hash_algorithm = self.cfg['hash_algorithm']
        self.filters = self.cfg['filters']

        self.data = {}
        self.data_file = ''

        self.preCheck()

    def preCheck(self):
        """
        Pre-check the destination status, i.e, whether a status file exists and ok.
        If not, it will be generated.
        """

        if not self.dst.exists():
            logging.warning(f'{self.dst} not exist, creating...')
            os.makedirs(self.dst.absolute(), exist_ok=True)

        hash_status = self.hashFileCheck()
        match hash_status:
            case 0:
                self.genHashFile()
            case 1:
                ...
            case _:
                if hash_status > 1 or hash_status < 0:
                    logging.error(f'Exit Code with HASH STATUS {hash_status}!')
                    exit()
        logging.info('Pre-Check successfully!')

    def hashFileCheck(self) -> int:
        """
        Check whether destination folder's status file is ok.

        For simple, here I check the filename == file.hash_digest to determine whether it's modified.

        Returns
        -------
        int
            hash file status:
            > 1 : more than 1 file exists, need manually operations.
            1   : ok
            -1  : file changed unexpectedly
            0   : file does not exist
        """
        folder = Path(self.dst)
        glob_list = glob(os.path.realpath(folder) + '/*.yml')
        data_file_num = len(glob_list)
        if data_file_num > 1:
            print(f'File Record Error! 1 needed but {data_file_num} exists!')
            return data_file_num
        elif data_file_num == 1:
            self.data_file = glob_list[0]
            logging.info(f'data file detected: {self.data_file}')
            with open(folder / self.data_file, 'r', encoding='utf-8') as r:
                hash_peep = yaml.load(r)
                data_len = len(hash_peep)
                logging.info(f'files count hashed: {data_len}')
            data_file_hash = hashFile(folder / self.data_file, algorithm=self.hash_algorithm)
            logging.info(f'stat file hash: {data_file_hash}')
            stem_of_rec_file = Path(self.data_file).stem
            logging.info(f'stat file stem: {stem_of_rec_file}')
            _files = os.listdir(folder)
            l1 = len(_files) - 1
            logging.info(f'pic file num: {l1}')
            if data_file_hash != stem_of_rec_file:
                logging.error('CODE -1 : HASH RECORD might has been modified unexpectedly, please manually check or delete it!')
                return -1
            if data_len != l1:
                logging.error('CODE -2 : HASH record and file nums not match!')
                return -2

            self.data = hash_peep
            return 1
            logging.info(f'Record file {self.data_file} checking successfully!')

        else:
            logging.warning('Code 0: File Record does not exist! It will be created in the following steps.')
            return 0

    def genHashFile(self):
        """
        Generate a hash file

        Returns
        -------
        Path
            The generated file path.
        """
        logging.info(f'Re-hashing pics in {self.dst} ...')
        self.protect('yEs')
        files = os.listdir(self.dst)
        count = len(files)
        logging.info(f'GEN-HASH-FILE: {count} files found.')
        _cnt = 0
        _failed_cnt = 0
        for i in range(0, count):
            print(i)
            f = files[i]
            fn = self.dst / f
            print(fn)
            f_stat = self.picEval(fn)
            print(f_stat)
            if f_stat != {}:
                if fn.stem != f_stat['stem']:
                    new_fn = self.dst / f'{f_stat["stem"]}.{f_stat["file_type"]}'
                    logging.info(f'{fn}, filename corrected to :{new_fn}')
                    os.rename(fn, new_fn)
                # mind the indent level!!! the following codes are out the prior if-statement
                self.data[f_stat['stem']] = f_stat
                _cnt += 1
                logging.info(f'{_cnt}/{count} old files checked')
            else:
                failed_dir = self.dst / 'FAILED_FILES_OF_PICGAZ'
                os.makedirs(failed_dir.absolute(), exist_ok=True)
                new_fn = failed_dir / fn.name
                _failed_cnt += 1
                logging.info(f'{_failed_cnt} files eval failed, it has been moved and new path is: {new_fn}')
                shutil.move(fn, new_fn)
        self.data_file = self.dst / 'tmp.yml'
        self.dump()

    def protect(self, word: str):
        """
        protect from damaging files in the next steps with a prompt word.

        Parameters
        ----------
        word : str
            the given protect word as a prompt, if correct, then continue.
            <enter> or others to exit.
        """
        prompt = input(f'{self.dst} files will be re-hashing and might be renamed, type f"{word}" to continue, <enter> or any other keys to break and exit:')
        if prompt != 'yEs':
            logging.error('ERROR: User break the process and exited after inputting {prompt}.')
            exit()

    def do(self):
        logging.info(f'Copying pics: {self.src} -> {self.dst} ...')
        _count = 0
        for i in os.listdir(self.src):
            f = self.src / i
            f_sta = self.picEval(f)
            if f_sta != {}:
                h = f_sta['stem']
                if h not in self.data:
                    nf = self.dst / f'{h}.{f_sta["file_type"]}'
                    logging.info(f'copying {f} --> {nf}')
                    shutil.copy(f, nf)
                    # key data adding...
                    self.data[h] = f_sta
                    _count += 1
                    logging.info(f'{_count} new files added.')

        logging.info(f'{_count} file(s) added.')
        if _count > 0:
            self.dump()

    def dump(self):
        with open(self.data_file, 'w', encoding='utf-8', newline='\n') as yw:
            yaml.dump(self.data, yw)
        new_data_file = self.dst / f'{hashFile(self.data_file,algorithm=self.hash_algorithm)}.yml'
        os.rename(self.data_file, new_data_file)  # Don't forget this step!
        self.data_file = new_data_file
        logging.info(f'data file dump successfully. {self.data_file}')

    def picEval(self, file: Path) -> dict:
        r = {}
        try:
            if file.exists():
                ext = picExt(file)
                if ext != '':
                    sz = Image.open(file).size
                    if min(sz) >= self.filters['min_border_px']:
                        r = {
                            'stem': hashFile(file, algorithm=self.hash_algorithm),
                            'update_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
                            'file_type': ext,
                            'file_size': os.path.getsize(file),
                            'width': sz[0],
                            'height': sz[1]
                        }
            return r
        except:
            logging.error(format_exc())
            return r


if __name__ == '__main__':
    config_file = Path(__file__).parent / 'picGaz.conf.yml'
    with open(config_file, 'r', encoding='utf8') as yr:
        config = yaml.load(yr)

    for p in config['plans']:
        sanction = UNIQUE_PIC_COPY(p)
        sanction.do()
