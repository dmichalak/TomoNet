from PyQt5.QtCore import QThread
import os, glob
import logging
import subprocess
import json

class Predict_network(QThread):

    def __init__(self, d):
        super().__init__()
        self.d = d
        self.log_file = "Autopick/autopick.log"
        self.pool = None
        
        self.logger = logging.getLogger(__name__)
        handler = logging.FileHandler(filename=self.log_file, mode='a')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        formatter.datefmt = "%y-%m-%d %H:%M:%S"
        self.logger.handlers = [handler]
        self.logger.setLevel(logging.INFO)

    def run(self):
        tomo_list = self.get_tomo_list(self.d['input_folder_predict'])
        #print(tomo_list)
        mask_list = []
        for tomo in tomo_list:
            if tomo.endswith(".mrc"):
                prefix = tomo.split(".mrc")[0]
                suffix = ".mrc"
            else:
                prefix = tomo.split(".rec")[0]
                suffix = ".rec"

            mask_file = "{}_mask{}".format(prefix, suffix)
            if os.path.exists(mask_file):
                mask_list.append(mask_file)
            else:
                mask_list.append(None)
        input_model = self.d['input_model']
        result_path = os.path.dirname(input_model)
        if result_path == "":
            result_path = os.getcwd()
        #predict_result_path = "{}/predict_result-{date:%Y-%m-%d_%H-%M}".format(result_path, date=datetime.datetime.now())
        predict_result_path = "{}/predict_result_box@{}_unitSize@{}_minPatch@{}_labelSize@{}_tol@{}_olSize@{}".format(result_path, \
            self.d['box_size_predict'], self.d['unit_size_predict'], self.d['min_patch_size_predict'],self.d['y_label_size_predict'],self.d['tolerance'],self.d['margin'])

        for i, tomo in enumerate(tomo_list):
            margin = self.d['margin']
            cmd = "predict_tomo_picking_ts.py {} {} {} {} {} {} {} {} {} {} {}".\
                format(tomo, predict_result_path, input_model, self.d['box_size_predict'], self.d['box_size_predict']-margin,\
                mask_list[i], self.d['unit_size_predict'], self.d['min_patch_size_predict'], self.d['y_label_size_predict'], self.d['tolerance'], self.log_file)
            if self.d['checkBox_print_only_predict_network']:
                cmd = "predict_tomo_picking_ts.py {} {} {} {} {} {} {} {} {} {}".\
                    format(tomo, predict_result_path, input_model, self.d['box_size_predict'], self.d['box_size_predict']-margin,\
                    mask_list[i], self.d['unit_size_predict'], self.d['min_patch_size_predict'], self.d['y_label_size_predict'], self.d['tolerance'])
                self.logger.info("########cmd for network predicting: {}########".format(os.path.basename(tomo)))
                self.logger.info(cmd)
            else:
                subprocess.run(cmd, shell=True, encoding="utf-8", stdout=open(self.log_file, 'a'))
        
                with open("{}/param.json".format(predict_result_path), 'w') as fp:
                    json.dump(self.d, fp, indent=2, default=int)        
        
    def get_tomo_list(self, folder):

        rec_files = set(glob.glob("{}/*.rec".format(folder)))
        tomo_files = set(glob.glob("{}/*.mrc".format(folder)))
        tomo_files.update(rec_files)
        tomo_files = list(tomo_files)
        tomo_files_filtered = []
        for tomo in tomo_files:
            if "mask" not in tomo:
                tomo_files_filtered.append(tomo)
        return sorted(tomo_files_filtered)

    def stop_process(self):

        import psutil, time
        self.terminate()
        self.quit()
        self.wait()
        
        # while True:
        #     a = [p.info['pid'] for p in psutil.process_iter(attrs=['pid', 'name']) if ('python' == p.info['name'] or 'python3' == p.info['name'])]
        #     print(a)
        #     if len(a) > 0:
        #         [p.kill() for p in psutil.process_iter(attrs=['pid', 'name']) if ('python' == p.info['name'] or 'python3' == p.info['name'])]
        #     else:
        #         break
        #     time.sleep(3)