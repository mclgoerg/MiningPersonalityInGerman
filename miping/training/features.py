import numpy as np

from sklearn.preprocessing import FunctionTransformer
from sklearn.pipeline import Pipeline
from sklearn.pipeline import FeatureUnion
from sklearn.preprocessing import StandardScaler

from ..models.profile import Profile
from ..interfaces.helper import Helper
from ..interfaces.glove import GloVe
from .noGloveValueError import NoGloveValueError


class Features:
    """
    Contains all pipeline functions for both LIWC and glove.
    """

    def __init__(
        self,
    ):
        return

    def featureLIWC(
        self,
        profileCol,
    ):
        """
        Extract LIWC features (namely LIWC categories) from
        each profile in list as feature.

        Parameters
        ----------
        profileCol : list, default=None, required
            List with profiles to generate features for.

        Returns
        -------
        np.array(outputList) : numpy.array
            Generated features in numpy format.
        """
        # will contain the LIWC measures for each profile
        outputList = []

        # loop over profileCollection
        for profile in profileCol:
            # create row
            liwc_data = []
            # get names of liwc categories
            for attrName in Profile.liwc_category_list:
                # get value of current category
                attr = getattr(profile, attrName)
                # append to current profile
                # and convert to float
                liwc_data.append(np.float(attr))

            outputList.append(liwc_data)

        # create numpy array, as scikit needs this format
        return np.array(outputList)

    def createLIWCFeaturePipeline(
        self,
    ):
        """
        Create pipeline that can be passed into multiple training procceses
        this is just a blueprint for calculating the features
        no features are calculated yet!

        Returns
        -------
        featurePipeline : Pipeline
            Pipeline containing feature generation and scaling.
        """

        # Create skicit-learn compatible FunctionTransformers
        # for usage with other sklearn functions
        # featureLIWC is the name of the function to be called to
        # extract features
        liwc_Trans = FunctionTransformer(self.featureLIWC, validate=False)

        # Combine feature(s) with FeatureUnion
        featureTransformer = FeatureUnion([
                                ('liwc', liwc_Trans),
                                ], n_jobs=-1)  # parallelize via multiprocess

        # combine into a pipeline including scaling
        featurePipeline = Pipeline([
                ('features', featureTransformer),
                ("stdScaler", StandardScaler())
        ])

        return featurePipeline

    def _condenseGloVeVectors(
        self,
        vectorList,
    ):
        """
        For each user a vectorList is passed in with different length.
        This will be condensed into a single 900 dim vector.
        """

        # convert to np array for mean,max,min functions
        vectorList = np.array(vectorList)

        # correct structure from (1,x,300) to (x,300)
        vectorList = vectorList[0]

        # for each dimension identify mean,max,min
        # and save in separate vector
        meanVector = vectorList.mean(axis=0)
        maxVector = np.amax(a=vectorList, axis=0)
        minVector = np.amin(a=vectorList, axis=0)

        # combine all 300 dim vectors in 900 dim vector
        returnVector = []
        returnVector.extend(meanVector)
        returnVector.extend(maxVector)
        returnVector.extend(minVector)

        # convert to numpy array for scikit
        returnVector = np.array(returnVector)

        return returnVector

    def featureGloVe(
        self,
        profileList,
    ):
        """
        For each profile in profile list generate GloVe features.

        Each profile contains text and for this text the glove vectors
        are retrieved and condensed into one single vector for this user.
        All user vectors are appended into the outputList.

        The word coverageStatistics and wordCounts for each user
        are saved in this feature object instance to be retrieved later.

        Parameters
        ----------
        profileList : list, default=None, required
            List containing relevant profiles for which to extract features.

        Returns
        -------
        np.array(outputList) : numpy.array
            Features in correct output format.
        """

        if self.glove is None:
            raise Exception("GloVe not loaded.")

        # will contain the GloVe measures for each profile
        outputList = []

        # get index as list, for faster lookup
        index_as_list = self.glove.get_index_list()

        # initialize progress bar
        helper = Helper()
        numProfiles = len(profileList)
        helper.printProgressBar(
            0,
            numProfiles,
            prefix='Progress:',
            suffix='Complete',
            length=50
        )

        # list for saving coverage statistics
        coverageStatistics = []
        # word count, that are included, for profiles
        wordCounts = []

        # loop over profileList
        for num, profile in enumerate(profileList):
            # tokenize text in tweets
            # separated by space
            tokens = profile.text.split(' ')

            profile_vectors = []

            # for each word lookup glove vector
            # if no match -> ignore it
            # first identify set of words not in glove
            not_in_glove = set(np.setdiff1d(tokens, index_as_list))

            # get words in glove, indcluding duplicates
            # so if words exist n times in text, they will be n times in list
            in_glove = [word for word in tokens if word not in not_in_glove]

            if len(in_glove) == 0:
                # es konnte kein wort in glove gefunden werden
                # raise Exception
                eString = (
                    "Could not find any glove values for given words"
                )
                raise NoGloveValueError(eString)
            else:
                # mind. ein Wort wurde gefunden
                # lookup glove vectors
                # should return duplicates!
                glove_values = self.glove.getGloVeByWordList(
                    wordList=in_glove
                )
                converted_vals = np.array(glove_values)
                # add vectors to list of this profile's vectors
                profile_vectors.append(converted_vals)

                # fill coverage statistics as share of tokens (=words)
                # that exist in glove in comparison to total tokens
                profile_coverage = len(converted_vals) / len(tokens)
                # add to global list
                coverageStatistics.append(profile_coverage)
                wordCounts.append(len(tokens))

                # after all vectors for this profile are retrieved
                # condense with maximum, minimum, average in 900 dim vector
                final_vector = self._condenseGloVeVectors(profile_vectors)

                # add 900 dim to output list
                outputList.append(final_vector)

            # Update Progress Bar
            helper.printProgressBar(
                num + 1,
                numProfiles,
                prefix='Progress:',
                suffix='Complete',
                length=50
            )

        # save coverage statistics in class attribute to be accessible
        self.coverageStatistics = coverageStatistics
        self.wordCounts = wordCounts

        # create numpy array, as scikit needs this format
        return np.array(outputList)

    def createGloVeFeaturePipeline(
        self,
        glovePath='data/glove/glove.db',
        dataBaseMode=True,
    ):
        """
        Create pipeline that can be passed into multiple training procceses
        this is just a blueprint for calculating the features
        no features are calculated yet!

        No parallelization (n_jobs=1) due to GloVe lookup in database.

        Parameters
        ----------
        glovePath : string, default='data/glove/glove.db'
            Path to GloVe flat or database file.
        dataBaseMode : boolean, default=True
            If True path points to SQLite database file.

        Returns
        -------
        featurePipeline : Pipeline
            Pipeline containing feature generation.
        """

        glove = GloVe(
            filePath=glovePath,
            dataBaseMode=dataBaseMode,
        )
        self.glove = glove

        # Create skicit-learn compatible FunctionTransformers
        # for usage with other sklearn functions
        # featureGloVe is the name of the function to be called to
        # extract features
        glove_Trans = FunctionTransformer(self.featureGloVe, validate=False)

        # Combine feature(s) with FeatureUnion
        featureTransformer = FeatureUnion([
                                ('glove', glove_Trans),
                                ], n_jobs=1)  # no parallelization

        # combine into a pipeline, no scaling since GloVe is scaled
        featurePipeline = Pipeline([
                ('features', featureTransformer)
        ])

        return featurePipeline
